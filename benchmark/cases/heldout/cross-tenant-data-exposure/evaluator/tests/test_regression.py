from rest_framework.test import APITestCase

from api.models import Project, Tenant


class TenantProjectIsolationOracleTests(APITestCase):
    def setUp(self):
        self.alpha = Tenant.objects.create(name="Synthetic Alpha")
        self.beta = Tenant.objects.create(name="Synthetic Beta")
        self.alpha_project = Project.objects.create(
            tenant=self.alpha,
            name="Alpha Public Project",
            confidential_summary="alpha-only synthetic summary",
        )
        self.beta_project = Project.objects.create(
            tenant=self.beta,
            name="Beta Confidential Project",
            confidential_summary="beta-only synthetic summary",
        )

    def get_project(self, project, tenant):
        return self.client.get(
            f"/api/projects/{project.pk}/",
            HTTP_X_TENANT_ID=str(tenant.pk),
        )

    def test_cross_tenant_project_is_indistinguishable_from_missing(self):
        response = self.get_project(self.beta_project, self.alpha)

        self.assertEqual(response.status_code, 404)
        self.assertNotIn("Beta Confidential", response.content.decode())
        self.assertNotIn("beta-only", response.content.decode())

    def test_each_tenant_can_retrieve_its_own_project(self):
        alpha_response = self.get_project(self.alpha_project, self.alpha)
        beta_response = self.get_project(self.beta_project, self.beta)

        self.assertEqual(alpha_response.status_code, 200)
        self.assertEqual(alpha_response.json()["name"], "Alpha Public Project")
        self.assertEqual(beta_response.status_code, 200)
        self.assertEqual(beta_response.json()["name"], "Beta Confidential Project")

    def test_unknown_project_remains_not_found(self):
        response = self.client.get(
            "/api/projects/99999/",
            HTTP_X_TENANT_ID=str(self.alpha.pk),
        )
        self.assertEqual(response.status_code, 404)

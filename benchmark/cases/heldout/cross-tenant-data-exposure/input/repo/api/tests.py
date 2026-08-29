from rest_framework.test import APITestCase

from .models import Project, Tenant


class ProjectDetailSmokeTests(APITestCase):
    def test_tenant_can_retrieve_its_project(self):
        tenant = Tenant.objects.create(name="Synthetic Tenant")
        project = Project.objects.create(
            tenant=tenant,
            name="Synthetic Project",
            confidential_summary="synthetic summary",
        )

        response = self.client.get(
            f"/api/projects/{project.pk}/",
            HTTP_X_TENANT_ID=str(tenant.pk),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["name"], "Synthetic Project")

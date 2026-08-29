from rest_framework.test import APITestCase

from api.models import Expense, Project, ProjectMembership, StaffUser, Tenant


class ProjectScopedApprovalOracleTests(APITestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Synthetic Tenant")
        self.manager = StaffUser.objects.create(
            tenant=self.tenant,
            name="Synthetic Manager",
        )
        self.alpha = Project.objects.create(tenant=self.tenant, name="Project Alpha")
        self.beta = Project.objects.create(tenant=self.tenant, name="Project Beta")
        ProjectMembership.objects.create(
            project=self.alpha,
            user=self.manager,
            role=ProjectMembership.MANAGER,
        )
        self.alpha_expense = Expense.objects.create(
            tenant=self.tenant,
            project=self.alpha,
            description="Alpha synthetic expense",
            amount_cents=1000,
        )
        self.beta_expense = Expense.objects.create(
            tenant=self.tenant,
            project=self.beta,
            description="Beta synthetic expense",
            amount_cents=2000,
        )

    def approve(self, expense):
        return self.client.post(
            f"/api/expenses/{expense.pk}/approve/",
            HTTP_X_TENANT_ID=str(self.tenant.pk),
            HTTP_X_USER_ID=str(self.manager.pk),
        )

    def test_manager_cannot_approve_sibling_project_expense(self):
        response = self.approve(self.beta_expense)

        self.assertEqual(response.status_code, 403)
        self.beta_expense.refresh_from_db()
        self.assertEqual(self.beta_expense.status, Expense.PENDING)
        self.assertIsNone(self.beta_expense.approved_by_id)

    def test_manager_can_still_approve_assigned_project_expense(self):
        response = self.approve(self.alpha_expense)

        self.assertEqual(response.status_code, 200)
        self.alpha_expense.refresh_from_db()
        self.assertEqual(self.alpha_expense.status, Expense.APPROVED)
        self.assertEqual(self.alpha_expense.approved_by_id, self.manager.pk)

    def test_contributor_membership_on_target_does_not_expand_manager_scope(self):
        ProjectMembership.objects.create(
            project=self.beta,
            user=self.manager,
            role=ProjectMembership.CONTRIBUTOR,
        )

        response = self.approve(self.beta_expense)

        self.assertEqual(response.status_code, 403)
        self.beta_expense.refresh_from_db()
        self.assertEqual(self.beta_expense.status, Expense.PENDING)

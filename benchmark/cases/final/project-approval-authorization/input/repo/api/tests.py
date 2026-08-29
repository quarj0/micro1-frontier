from rest_framework.test import APITestCase

from .models import Expense, Project, ProjectMembership, StaffUser, Tenant


class ExpenseApprovalSmokeTests(APITestCase):
    def test_project_manager_can_approve_project_expense(self):
        tenant = Tenant.objects.create(name="Synthetic Tenant")
        manager = StaffUser.objects.create(tenant=tenant, name="Synthetic Manager")
        project = Project.objects.create(tenant=tenant, name="Synthetic Project")
        ProjectMembership.objects.create(
            project=project,
            user=manager,
            role=ProjectMembership.MANAGER,
        )
        expense = Expense.objects.create(
            tenant=tenant,
            project=project,
            description="Synthetic expense",
            amount_cents=5000,
        )

        response = self.client.post(
            f"/api/expenses/{expense.pk}/approve/",
            HTTP_X_TENANT_ID=str(tenant.pk),
            HTTP_X_USER_ID=str(manager.pk),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], Expense.APPROVED)
        self.assertEqual(response.json()["approved_by"], manager.pk)

from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Expense, ProjectMembership, StaffUser, Tenant


def numeric_header(request, name):
    try:
        return int(request.headers.get(name))
    except (TypeError, ValueError) as exc:
        raise ValidationError({name: "A numeric header is required."}) from exc


class ExpenseApprovalView(APIView):
    def post(self, request, expense_id):
        tenant = get_object_or_404(Tenant, pk=numeric_header(request, "X-Tenant-ID"))
        user = get_object_or_404(
            StaffUser,
            pk=numeric_header(request, "X-User-ID"),
            tenant=tenant,
        )
        expense = get_object_or_404(Expense, pk=expense_id, tenant=tenant)
        can_approve = ProjectMembership.objects.filter(
            user=user,
            role=ProjectMembership.MANAGER,
        ).exists()
        if not can_approve:
            raise PermissionDenied("Project manager access is required.")

        expense.status = Expense.APPROVED
        expense.approved_by = user
        expense.save(update_fields=("status", "approved_by"))
        return Response(
            {
                "id": expense.pk,
                "status": expense.status,
                "approved_by": expense.approved_by_id,
            }
        )

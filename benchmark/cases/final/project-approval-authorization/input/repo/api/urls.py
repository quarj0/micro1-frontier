from django.urls import path

from .views import ExpenseApprovalView

urlpatterns = [
    path(
        "expenses/<int:expense_id>/approve/",
        ExpenseApprovalView.as_view(),
        name="expense-approve",
    )
]

from django.db import models


class Tenant(models.Model):
    name = models.CharField(max_length=80)


class StaffUser(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    name = models.CharField(max_length=80)


class Project(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    name = models.CharField(max_length=120)


class ProjectMembership(models.Model):
    MANAGER = "manager"
    CONTRIBUTOR = "contributor"
    ROLE_CHOICES = [(MANAGER, "Manager"), (CONTRIBUTOR, "Contributor")]

    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    user = models.ForeignKey(StaffUser, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("project", "user"),
                name="unique_project_membership",
            )
        ]


class Expense(models.Model):
    PENDING = "pending"
    APPROVED = "approved"

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    description = models.CharField(max_length=160)
    amount_cents = models.PositiveIntegerField()
    status = models.CharField(max_length=20, default=PENDING)
    approved_by = models.ForeignKey(
        StaffUser,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="approved_expenses",
    )

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Charge, Tenant


def charge_payload(charge, replayed):
    return {
        "id": charge.pk,
        "tenant_id": charge.tenant_id,
        "amount_cents": charge.amount_cents,
        "replayed": replayed,
    }


class ChargeCreateView(APIView):
    def post(self, request):
        tenant = get_object_or_404(Tenant, pk=request.headers.get("X-Tenant-ID"))
        key = request.headers.get("Idempotency-Key")
        if not key:
            raise ValidationError({"idempotency_key": "This header is required."})
        try:
            amount_cents = int(request.data["amount_cents"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValidationError({"amount_cents": "A positive integer is required."}) from exc
        if amount_cents <= 0:
            raise ValidationError({"amount_cents": "A positive integer is required."})

        existing = Charge.objects.filter(idempotency_key=key).first()
        if existing is not None:
            return Response(charge_payload(existing, replayed=True))

        charge = Charge.objects.create(
            tenant=tenant,
            idempotency_key=key,
            amount_cents=amount_cents,
        )
        return Response(charge_payload(charge, replayed=False), status=status.HTTP_201_CREATED)

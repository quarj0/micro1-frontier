from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import UploadedDocument


def document_payload(document):
    return {
        "id": document.pk,
        "filename": document.filename,
        "content_type": document.content_type,
        "size_bytes": document.size_bytes,
    }


class DocumentUploadView(APIView):
    parser_classes = [JSONParser]

    def get(self, request):
        documents = UploadedDocument.objects.order_by("pk")
        return Response([document_payload(document) for document in documents])

    def post(self, request):
        uploaded = request.FILES.get("file")
        if uploaded is None:
            raise ValidationError({"file": "A file part is required."})
        document = UploadedDocument.objects.create(
            filename=uploaded.name,
            content_type=uploaded.content_type or "application/octet-stream",
            size_bytes=uploaded.size,
        )
        return Response(document_payload(document), status=status.HTTP_201_CREATED)

from rest_framework.test import APITestCase

from .models import UploadedDocument


class DocumentUploadSmokeTests(APITestCase):
    def test_list_returns_stored_metadata(self):
        document = UploadedDocument.objects.create(
            filename="synthetic-existing.txt",
            content_type="text/plain",
            size_bytes=12,
        )

        response = self.client.get("/api/uploads/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            [
                {
                    "id": document.pk,
                    "filename": "synthetic-existing.txt",
                    "content_type": "text/plain",
                    "size_bytes": 12,
                }
            ],
        )

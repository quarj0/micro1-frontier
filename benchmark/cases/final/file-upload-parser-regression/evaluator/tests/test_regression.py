from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase

from api.models import UploadedDocument


class MultipartUploadOracleTests(APITestCase):
    def test_multipart_file_is_accepted_and_metadata_is_stored(self):
        uploaded = SimpleUploadedFile(
            "synthetic-report.txt",
            b"synthetic upload body\n",
            content_type="text/plain",
        )

        response = self.client.post(
            "/api/uploads/",
            {"file": uploaded},
            format="multipart",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["filename"], "synthetic-report.txt")
        self.assertEqual(response.json()["content_type"], "text/plain")
        self.assertEqual(response.json()["size_bytes"], 22)
        document = UploadedDocument.objects.get()
        self.assertEqual(document.filename, "synthetic-report.txt")
        self.assertEqual(document.size_bytes, 22)

    def test_missing_file_reaches_validation_instead_of_parser_rejection(self):
        response = self.client.post("/api/uploads/", {}, format="multipart")

        self.assertEqual(response.status_code, 400)
        self.assertIn("file", response.json())

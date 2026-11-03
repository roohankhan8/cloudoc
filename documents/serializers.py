from pathlib import Path
import uuid

from django.conf import settings
from rest_framework import serializers

from .models import Document
from .storage import create_download_url, delete_document, upload_document


class DocumentSerializer(serializers.ModelSerializer):
    file = serializers.FileField(write_only=True, required=True)
    download_url = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = ["id", "original_filename", "content_type", "size", "created_at", "download_url", "file"]
        read_only_fields = ["id", "original_filename", "content_type", "size", "created_at", "download_url"]

    def validate_file(self, value):
        allowed_extensions = {".pdf", ".csv", ".xlsx"}
        if Path(value.name).suffix.lower() not in allowed_extensions:
            raise serializers.ValidationError("Only PDF, CSV, and XLSX files are supported.")
        if value.size > settings.MAX_UPLOAD_SIZE:
            raise serializers.ValidationError(f"File must be {settings.MAX_UPLOAD_SIZE} bytes or smaller.")
        return value

    def create(self, validated_data):
        file_obj = validated_data.pop("file")
        original_filename = Path(file_obj.name).name[:255]
        object_key = f"documents/{uuid.uuid4()}{Path(original_filename).suffix.lower()}"
        upload_document(file_obj, object_key)
        try:
            return Document.objects.create(
                original_filename=original_filename,
                object_key=object_key,
                content_type=file_obj.content_type or "application/octet-stream",
                size=file_obj.size,
            )
        except Exception:
            delete_document(object_key)
            raise

    def get_download_url(self, obj):
        return create_download_url(obj.object_key)

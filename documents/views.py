from django.shortcuts import redirect
from rest_framework import viewsets

from .models import Document
from .serializers import DocumentSerializer
from .storage import delete_document


class DocumentViewSet(viewsets.ModelViewSet):
    serializer_class = DocumentSerializer
    http_method_names = ["get", "post", "delete", "head", "options"]

    def get_queryset(self):
        return Document.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        if response.status_code == 201 and request.accepted_media_type.startswith("text/html"):
            return redirect("document-list")
        return response

    def perform_destroy(self, instance):
        delete_document(instance.object_key)
        instance.delete()

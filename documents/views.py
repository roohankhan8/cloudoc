from rest_framework import viewsets

from .models import Document
from .serializers import DocumentSerializer
from .storage import delete_document


class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    http_method_names = ["get", "post", "delete", "head", "options"]

    def perform_destroy(self, instance):
        delete_document(instance.object_key)
        instance.delete()

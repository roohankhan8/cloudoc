from django.contrib import admin
from django.urls import include, path

from documents import web_views

urlpatterns = [
    path("", web_views.document_list, name="document-list"),
    path("documents/upload/", web_views.upload_document, name="document-upload"),
    path("documents/<uuid:document_id>/download/", web_views.download_document, name="document-download"),
    path("documents/<uuid:document_id>/delete/", web_views.delete_document, name="document-delete"),
    path("admin/", admin.site.urls),
    path("api/documents/", include("documents.urls")),
]

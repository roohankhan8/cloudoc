import logging

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST

from .models import Document
from .serializers import DocumentSerializer
from .storage import create_download_url, delete_document as delete_s3_document

logger = logging.getLogger(__name__)


@require_GET
def document_list(request):
    return render(request, "documents/index.html", {"documents": Document.objects.all()})


@require_POST
def upload_document(request):
    serializer = DocumentSerializer(data={"file": request.FILES.get("file")})
    if not serializer.is_valid():
        messages.error(request, serializer.errors["file"][0])
        return redirect("document-list")

    try:
        document = serializer.save()
    except Exception:
        logger.exception("Document upload failed.")
        messages.error(request, "Upload failed. Check that Floci and SQS are running, then try again.")
    else:
        messages.success(request, f"{document.original_filename} uploaded and queued for processing.")
    return redirect("document-list")


@require_GET
def download_document(request, document_id):
    document = get_object_or_404(Document, pk=document_id)
    return redirect(create_download_url(document.object_key))


@require_POST
def delete_document(request, document_id):
    document = get_object_or_404(Document, pk=document_id)
    try:
        delete_s3_document(document.object_key)
        document.delete()
    except Exception:
        logger.exception("Could not delete document %s.", document.id)
        messages.error(request, "Could not delete the document. Check that Floci is running, then try again.")
    else:
        messages.success(request, f"{document.original_filename} deleted.")
    return redirect("document-list")

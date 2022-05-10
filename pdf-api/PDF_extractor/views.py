from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from .serializers import UploadSerializer, UserSerializer
from .helpers import ExtractorController as ec
from .helpers import QRController as qc
from .Config import Paths
from django.http import HttpResponse
import os

# ViewSets define the view behavior.
class PDF_Extract_ViewSet(ViewSet):
    serializer_class = UploadSerializer
    permission_classes = (IsAuthenticated,)

    def list(self, request):
        return Response("Online")

    def create(self, request):
        file_uploaded = request.FILES.get('file')
        filename = file_uploaded.name
        with open(f"{Paths.pdf_path.value}/{filename}",  "wb") as f:
            for chunk in file_uploaded.chunks():
                f.write(chunk)
        
        data = ec().assign_to_extractor(filename)
        return Response(data)

# ViewSets define the view behavior.
class QR_ViewSet(ViewSet):
    serializer_class = UploadSerializer
    permission_classes = (IsAuthenticated,)

    @action(detail=True, methods=['get'])
    def get_file(self, request, filename):
        try:
            response = HttpResponse(open(f"{Paths.pdf_path.value}/{filename}", "rb"), content_type='application/pdf')
            response["Content-Disposition"] = 'attachment; filename="%s"' % filename
            os.remove(f"{Paths.pdf_path.value}/{filename}")
        except FileNotFoundError:
            return Response("File not found")
        return response

    def create(self, request):
        file_uploaded = request.FILES.get('file')
        filename = file_uploaded.name
        with open(f"documents/{filename}",  "wb") as f:
            for chunk in file_uploaded.chunks():
                f.write(chunk)
        
        response = qc().get_qr_from_document(filename)
        return Response(response)


class Userview(RetrieveAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user

    
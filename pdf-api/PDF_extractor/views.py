from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework.generics import RetrieveAPIView, UpdateAPIView, CreateAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import action
from rest_framework import status
from .serializers import UploadSerializer, UserSerializer, ChangePasswordSerializer, RegisterSerializer
from .helpers import ExtractorController as ec
from .helpers import QRController as qc
import gc
from .Config import Paths
from django.http import HttpResponse
from django.contrib.auth.models import User
import os

# ViewSets define the view behavior.
class PDF_Extract_ViewSet(ViewSet):
    """
    An endpoint extracting information from PDF (RC/PB/AK).
    """
    serializer_class = UploadSerializer
    permission_classes = (IsAuthenticated,)

    @action(detail=True, methods=['post'])
    def extract_data(self, request, filetype):
        file_uploaded = request.FILES.get('file')
        filename = file_uploaded.name
        with open(f"{Paths.pdf_path.value}/{filename}",  "wb") as f:
            for chunk in file_uploaded.chunks():
                f.write(chunk)
        data = ec().assign_to_extractor(filename, filetype)
        gc.collect()
        return Response(data)
        

# ViewSets define the view behavior.
class QR_ViewSet(ViewSet):
    """
    An endpoint for processing QR & returning remaining pages.
    """
    serializer_class = UploadSerializer
    permission_classes = (IsAuthenticated,)

    @action(detail=True, methods=['get'])
    def get_file(self, request, filename):
        try:
            response = HttpResponse(open(f"{Paths.pdf_path.value}/{filename}", "rb"), content_type='application/pdf')
            response["Content-Disposition"] = 'attachment; filename="%s"' % filename
            os.remove(f"{Paths.pdf_path.value}/{filename}")
            gc.collect()
        except FileNotFoundError:
            gc.collect()
            return Response("File not found")
        return response

    def create(self, request):
        file_uploaded = request.FILES.get('file')
        filename = file_uploaded.name
        with open(f"documents/{filename}",  "wb") as f:
            for chunk in file_uploaded.chunks():
                f.write(chunk)
        
        response = qc().get_qr_from_document(filename)
        gc.collect()
        return Response(response)


class Userview(RetrieveAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user

class RegisterView(CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer

class ChangePasswordView(UpdateAPIView):
    """
    An endpoint for changing password.
    """
    serializer_class = ChangePasswordSerializer
    model = User
    permission_classes = (IsAuthenticated,)

    def get_object(self, queryset=None):
        obj = self.request.user
        return obj

    def update(self, request, *args, **kwargs):
        self.object = self.get_object()
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            # Check old password
            if not self.object.check_password(serializer.data.get("old_password")):
                return Response({"old_password": ["Wrong password."]}, status=status.HTTP_400_BAD_REQUEST)
            # set_password also hashes the password that the user will get
            self.object.set_password(serializer.data.get("new_password"))
            self.object.save()
            response = {
                'status': 'success',
                'code': status.HTTP_200_OK,
                'message': 'Password updated successfully',
                'data': []
            }

            return Response(response)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


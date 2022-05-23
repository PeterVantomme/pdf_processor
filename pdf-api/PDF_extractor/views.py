from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework.generics import RetrieveAPIView, UpdateAPIView, CreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework import status
from .serializers import UploadSerializer, UserSerializer, ChangePasswordSerializer, RegisterSerializer
from .helpers import ExtractorController as ec
from .helpers import QRController as qc
from .Config import Paths
from django.http import HttpResponse
from django.contrib.auth.models import User
import os
import json

# View for getting information from PDF-documents, calls extractor and returns JSON.
class PDF_Extract_ViewSet(ViewSet):
    """
    An endpoint extracting information from PDF (RC/PB/AK).
    """
    serializer_class = UploadSerializer
    permission_classes = (IsAuthenticated,)

    @action(detail=True, methods=['post'])
    def extract_data(self, request, filetype):
        try:
            file_uploaded = request.FILES.get('file')
            filename = file_uploaded.name
            with open(f"{Paths.pdf_path.value}/{filename}",  "wb") as f:
                for chunk in file_uploaded.chunks():
                    f.write(chunk)
            response = Response(ec().assign_to_extractor(filename, filetype))
        except IndexError:
            response = HttpResponse(json.dumps(f"Check file type, is this a document of type {filetype}? (filename: {filename})"),status=status.HTTP_400_BAD_REQUEST)
            os.remove(f"{Paths.pdf_path.value}/{filename}")
        finally:
            return response
        
# View for reading QR-code from first page and returning the remaining pages.
class QR_ViewSet(ViewSet):
    """
    An endpoint for processing QR & returning remaining pages.
    """
    serializer_class = UploadSerializer
    permission_classes = (IsAuthenticated,)

    # Returns remaining pages of PDF-document and removes that document once it has been returned.
    @action(detail=True, methods=['get'])
    def get_file(self, request, filename):
        try:
            response = HttpResponse(open(f"{Paths.pdf_path.value}/{filename}", "rb"), content_type='application/pdf')
            response["Content-Disposition"] = 'attachment; filename="%s"' % filename
            os.remove(f"{Paths.pdf_path.value}/{filename}")
        except FileNotFoundError:
            response =  Response(json.dumps(f"File {filename} not found"),status=status.HTTP_404_NOT_FOUND)
        finally:
            return response

    # Returns JSON with content of the QR-code after processing.
    def create(self, request):
        try:
            file_uploaded = request.FILES.get('file')
            filename = file_uploaded.name
            with open(f"documents/{filename}",  "wb") as f:
                for chunk in file_uploaded.chunks():
                    f.write(chunk)
            
            response = Response(qc().get_qr_from_document(filename))
        except IndexError:
            response = HttpResponse(json.dumps(f"No QR-code detected on this document (filename: {filename})"),status=status.HTTP_400_BAD_REQUEST)
        finally:
            return response

# Returns data of the current user.
class Userview(RetrieveAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user

# Used for Registering new users.
class RegisterView(CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer

# Cleans up the whole "documents" folder.
class CleanupView(ViewSet):
    permission_classes = (IsAuthenticated,)

    @action(detail=False, methods=['delete'])
    def cleanup(self, request):
        files = os.listdir(Paths.pdf_path.value)
        for file in files:
            os.remove(f"{Paths.pdf_path.value}/{file}")
        filestring = "file" if len(files) == 1 else "files"
        return Response(json.dumps(f"Cleaned up {len(files)} {filestring}"), status=status.HTTP_200_OK)

# Changes current users' password.
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

            return Response(json.dumps(response))

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


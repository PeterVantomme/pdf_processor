from django.forms import CharField
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework.generics import RetrieveAPIView, UpdateAPIView, CreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.serializers import CharField
from rest_framework.decorators import action
from rest_framework import status
from .serializers import UploadSerializer, UserSerializer, ChangePasswordSerializer, RegisterSerializer, FileReturnSerializer, QRReturnSerializer, ExtractReturnSerializer
from .helpers import ExtractorController as ec
from .helpers import QRController as qc
from .helpers import OCRController as ocr
from .helpers import ErrorHelper as eh
from .Config import Paths
from django.http import FileResponse, HttpResponse
from django.contrib.auth.models import User
import os
import json
from fitz import FileDataError
from drf_spectacular.utils import extend_schema, inline_serializer
# View for getting information from PDF-documents, calls extractor and returns JSON.

class PDF_Extract_ViewSet(ViewSet):
    """
    Extracting of information from PDF file given the type of the document..
    """
    serializer_class = UploadSerializer
    permission_classes = (IsAuthenticated,)
    @extend_schema(responses={200:ExtractReturnSerializer, 
                              400:eh.get_400(),
                              402:eh.get_402()})
    @action(detail=True, methods=['post'])
    def extract_data(self, request, documenttype):
        try:
            file_uploaded = request.FILES.get('file_uploaded')
            filename = file_uploaded.name
            with open(f"{Paths.pdf_path.value}/{filename}",  "wb") as f:
                for chunk in file_uploaded.chunks():
                    f.write(chunk)
            response = Response(ec().assign_to_extractor(filename, documenttype))
        except IndexError or AttributeError:
            response = HttpResponse(json.dumps({"detail":f"Check document type, is this a document of type {documenttype}? (filename: {filename})"}),status=status.HTTP_400_BAD_REQUEST)
            os.remove(f"{Paths.pdf_path.value}/{filename}")
        except AttributeError:
            response = HttpResponse(json.dumps({"detail":f"No file found in request, make sure key value is 'file_uploaded'"}),status=status.HTTP_400_BAD_REQUEST)
        except NotImplementedError:
            response = HttpResponse(json.dumps({"detail":f"Document filetype of {filename} not supported"}),status=status.HTTP_400_BAD_REQUEST)
        finally:
            return response
        
# View for reading QR-code from first page and returning the remaining pages.
class QR_ViewSet(ViewSet):
    """
    Processing of QR-code on documents where first page contains a QR code for classifcation & returning remaining pages.
    """
    serializer_class = UploadSerializer
    permission_classes = (IsAuthenticated,)

    @extend_schema(description="Returns remaining pages of PDF-document and removes that document once it has been returned.",
                   responses={200: FileReturnSerializer,
                              404: eh.get_404(),
                              402: eh.get_402()})
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

    @extend_schema(description="Returns JSON with content of the QR-code after processing.",
                   responses={200:QRReturnSerializer, 
                              400:eh.get_400(),
                              402:eh.get_402()})
    def create(self, request):
        try:
            file_uploaded = request.FILES.get('file_uploaded')
            filename = file_uploaded.name
            with open(f"documents/{filename}",  "wb") as f:
                for chunk in file_uploaded.chunks():
                    f.write(chunk)
            response = Response(qc().get_qr_from_document(filename))
        except IndexError:
            response = HttpResponse(json.dumps(f"No QR-code detected on this document (filename: {filename})"),status=status.HTTP_400_BAD_REQUEST)
        except AttributeError:
            response = HttpResponse(json.dumps(f"No file found in request, make sure key value is 'file_uploaded'"),status=status.HTTP_400_BAD_REQUEST)
        except FileDataError:
            response = HttpResponse(json.dumps(f"{filename} is not a valid PDF document"),status=status.HTTP_400_BAD_REQUEST)
        finally:
            return response

class OCR_ViewSet(ViewSet):
    """
    Processing of scanned document, returns a pdf-file with selectable text.
    """
    serializer_class = UploadSerializer
    permission_classes = (IsAuthenticated,)
    @extend_schema(responses={200: FileReturnSerializer,
                              402: eh.get_402(),
                              400: eh.get_400()})
    @action(detail=False, methods=['post'])
    def convert_to_text(self, request):
        try:
            file_uploaded = request.FILES.get('file_uploaded')
            filename = file_uploaded.name
            with open(f"{Paths.pdf_path.value}/{filename}",  "wb") as f:
                for chunk in file_uploaded.chunks():
                    f.write(chunk)
            is_succeeded = ocr.convert(filename)
            if is_succeeded:
                response = FileResponse(open(f"{Paths.pdf_path.value}/{filename}", "rb"), content_type='application/pdf')
                os.remove(f"{Paths.pdf_path.value}/{filename}")
            else:
                raise IndexError()
        except IndexError:
            response = HttpResponse(json.dumps({"detail":f"Not able to convert to text (filename: {filename})"}),status=status.HTTP_400_BAD_REQUEST)
            os.remove(f"{Paths.pdf_path.value}/{filename}")
        except AttributeError:
            response = HttpResponse(json.dumps({"detail":"No file found in request, make sure key value is 'file_uploaded'"}),status=status.HTTP_400_BAD_REQUEST)
        except ReferenceError:
            response = HttpResponse(json.dumps({"detail":f"File not readable. Uploaded file must be a PDF-document (filename: {filename})"}),status=status.HTTP_400_BAD_REQUEST)
        except FileDataError:
            response = HttpResponse(json.dumps({"detail":f"File not readable. Uploaded file might be broken or not a PDF-document (filename: {filename})"}),status=status.HTTP_400_BAD_REQUEST)
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
    """
    Removes documents from the "documents" folder if they weren't requested.
    """
    permission_classes = (IsAuthenticated,)
    @extend_schema(responses={200: inline_serializer('FilesDeleted', fields={'message': CharField()}),
                              402: eh.get_402()})
    @action(detail=False, methods=['delete'])
    def cleanup(self, request):
        files = os.listdir(Paths.pdf_path.value)
        for file in files:
            os.remove(f"{Paths.pdf_path.value}/{file}")
        filestring = "file" if len(files) == 1 else "files"
        return Response(json.dumps({"message":f"Cleaned up {len(files)} {filestring}"}), status=status.HTTP_200_OK)

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

    @extend_schema(responses={200: inline_serializer('PasswordChanged', fields={'message': CharField()}),
                              400: eh.get_400()})
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

from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from .serializers import UploadSerializer, UserSerializer
from .helpers import ExtractorController as ec

# ViewSets define the view behavior.
class UploadViewSet(ViewSet):
    serializer_class = UploadSerializer
    permission_classes = (IsAuthenticated,)

    def list(self, request):
        return Response("Online")

    def create(self, request):
        file_uploaded = request.FILES.get('file')
        filename = file_uploaded.name
        with open(f"documents/{filename}",  "wb") as f:
            for chunk in file_uploaded.chunks():
                f.write(chunk)
        
        data = ec().assign_to_extractor(filename)
        return Response(data)

class Userview(RetrieveAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user

    
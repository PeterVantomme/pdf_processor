from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from .serializers import UploadSerializer
from .helpers import ExtractorController as ec

# ViewSets define the view behavior.
class UploadViewSet(ViewSet):
    serializer_class = UploadSerializer

    def list(self, request):
        return Response("GET API")

    def create(self, request):
        file_uploaded = request.FILES.get('file')
        filename = file_uploaded.name
        with open(f"documents/{filename}",  "wb") as f:
            for chunk in file_uploaded.chunks():
                f.write(chunk)
        
        data = ec().assign_to_extractor(filename)
        return Response(data)

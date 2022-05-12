from unittest.util import _MAX_LENGTH
from rest_framework.serializers import Serializer, FileField, ModelSerializer, CharField
from django.contrib.auth import get_user_model

# Serializers define the API representation.
class UploadSerializer(Serializer):
    file_uploaded = FileField()
    class Meta:
        fields = ['file_uploaded']

class UserSerializer(ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ['id','username']
    
class ChangePasswordSerializer(Serializer):
    model=get_user_model()
    old_password=CharField(required=True, max_length=32)
    new_password=CharField(required=True, max_length=32)
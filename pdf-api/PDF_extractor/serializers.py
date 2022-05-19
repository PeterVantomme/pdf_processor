from rest_framework.serializers import Serializer, FileField, ModelSerializer, CharField, EmailField, ValidationError
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.models import User
from rest_framework.validators import UniqueValidator
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
    
class RegisterSerializer(ModelSerializer):
    email = EmailField(
            required=True,
            validators=[UniqueValidator(queryset=User.objects.all())]
            )

    password = CharField(write_only=True, required=True, validators=[validate_password])
    password2 = CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('username', 'password', 'password2', 'email')


    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise ValidationError({"password": "Password fields didn't match."})

        return attrs

    def create(self, validated_data):
        user = User.objects.create(
            username=validated_data['username'],
            email=validated_data['email'],
        )

        user.set_password(validated_data['password'])
        user.save()

        return user

class ChangePasswordSerializer(Serializer):
    model=get_user_model()
    old_password=CharField(required=True, max_length=32)
    new_password=CharField(required=True, max_length=32)
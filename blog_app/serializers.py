from rest_framework import serializers
from django.contrib.auth.models import User

from .models import BlogPost

class SignUpSerializer(serializers.Serializer):
    username = serializers.CharField(max_length = 255, required = True)
    email = serializers.CharField(max_length = 255, required = True)
    password = serializers.CharField(max_length = 255, required = True)
    is_staff = serializers.BooleanField(default = False, required = False)
    is_active = serializers.BooleanField(default = True, required = False)

class SignInSerializers(serializers.Serializer):
    email = serializers.CharField(max_length = 255, required = True)
    password = serializers.CharField(max_length = 255, required = True)

class BlogPostSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255, allow_blank=True, required=False)
    content = serializers.CharField()
    image = serializers.ImageField(required = False) 
    created_at = serializers.DateTimeField(read_only=True)
    modified_at = serializers.DateTimeField(read_only=True)

class CommentSerializer(serializers.Serializer):
    content = serializers.CharField()
    
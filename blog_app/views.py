import os
from django.shortcuts import render
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.core.validators import validate_email
from django.core.exceptions import ValidationError as DjangoValidationError

from django.db import transaction
from django.contrib.auth.models import User
from django.utils.dateparse import parse_datetime
from django.db.models import Q

from .serializers import BlogPostSerializer, CommentSerializer, SignInSerializers, SignUpSerializer
from .models import BlogPost,Comment
from cloudinary.uploader import upload as cloudinary_upload

import cloudinary
import cloudinary.uploader
import cloudinary.api

cloudinary.config(
    cloud_name = 'darid8ehu',
    api_key = os.getenv("CLOUDINARY_API_KEY"),
    api_secret = os.getenv("CLOUDINARY_API_SECRET")
)

def cloudinary_upload(image_file):
    """Upload an image file to Cloudinary and return the result."""
    try:
        upload_result = cloudinary.uploader.upload(
            image_file,
            resource_type="auto"
        )
        return upload_result
    except Exception as e:
        print(f"Cloudinary upload error: {str(e)}")
        raise e

class SignUpApiView(GenericAPIView):
    serializer_class = SignUpSerializer
    permission_classes = (AllowAny,)

    def post(self, request):
        response = {}
        data = request.data
        serializer_data = self.get_serializer(data = data)
        if serializer_data.is_valid():
            try:
                with transaction.atomic():
                    valid_ser_data = serializer_data.validated_data
                    username = valid_ser_data.get('username')
                    email = valid_ser_data.get('email')
                    password = valid_ser_data.get('password')
                    name = username.split()
                    first_name = name[0] if len(name) > 1 else ""
                    last_name = name[1] if len(name) > 1 else ""

                    if email:
                        if not User.objects.filter(email = email).exists():
                            try:
                                validate_email(email)
                            except DjangoValidationError:
                                return Response({"email": "Invalid email format"}, status=status.HTTP_400_BAD_REQUEST)
                        else:
                            return Response({"message" : "Email already exists"}, status=status.HTTP_400_BAD_REQUEST)
                    else:
                        return Response(
                            {
                                "message" : "Please enter a mail",
                                "status" : False
                            },
                            status = status.HTTP_400_BAD_REQUEST
                        )
                    
                    if password:
                        if len(password) <= 6:
                            return Response({"message" : "Password must be 6 letters"}, status=status.HTTP_400_BAD_REQUEST)
                        user = User(username=username, email=email, first_name=first_name, last_name=last_name)
                        user.set_password(password)
                        user.save()

                        user = authenticate(request, username=username, password=password)
                        if user is not None:
                            refresh = RefreshToken.for_user(user)
                            response['message'] = 'User created and authenticated successfully'
                            response['status'] = True
                            response['access'] = str(refresh.access_token)
                            response['refresh'] = str(refresh)

                            return Response(response, status=status.HTTP_201_CREATED)
                        else:
                            return Response({"message": "Authentication failed", "status": False}, status=status.HTTP_401_UNAUTHORIZED)
                    else:
                        return Response({"message": "Please enter a password", "status": False}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                return response({"error" : str(e)}, status=status.HTTP_406_NOT_ACCEPTABLE)
        else:
            return Response({"error" : serializer_data.errors,"message" : "Something went wrong"},status=status.HTTP_400_BAD_REQUEST)
        
class SignInApiView(GenericAPIView):
    serializer_class = SignInSerializers
    permission_classes = (AllowAny,)

    def post(self, request):
        response = {}
        data = request.data
        serializer_data = self.get_serializer(data = data)
        if serializer_data.is_valid():
            email = serializer_data.validated_data.get('email')
            password = serializer_data.validated_data.get("password")

            if (email and password):
                user = User.objects.filter(email = email).last()
                if not user:
                    return Response({
                        "message" : "Email does not exists",
                        "status" : False
                    }, status=status.HTTP_401_UNAUTHORIZED)
                
                user = authenticate(username=user.username, password=password)
                if user is not None:
                    refresh = RefreshToken.for_user(user)
                    response = {
                        "message": "Login successful",
                        "access": str(refresh.access_token),
                        "refresh": str(refresh),
                        "user": {
                            "username": user.username,
                            "email": user.email,
                            "first_name": user.first_name,
                            "last_name": user.last_name
                        }
                    }
                    return Response(response, status=status.HTTP_200_OK)
                else:
                    return Response({"message": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
        else:
            return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        
class BlogPostApiView(GenericAPIView):
    serializer_class = BlogPostSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        print(request.user)
        data = request.data.copy()
        serializer = self.get_serializer(data=data)

        if serializer.is_valid():
            try:
                with transaction.atomic():
                    valid_data = serializer.validated_data
                    image_file = request.FILES.get('image')  
                    if image_file:
                        uploaded_image = cloudinary_upload(image_file)
                        image_url = uploaded_image.get('secure_url')
                        data['image'] = image_url
                    else:
                        image_url = None

                    if BlogPost.objects.filter(content=valid_data.get('content')).exists():
                        existing = BlogPost.objects.get(content=valid_data.get('content'))
                        return Response({
                            'message': 'Blog with this content already exists',
                            'author': existing.author.username
                        }, status=400)

                    blog_post = BlogPost.objects.create(
                        title=valid_data.get('title', ''),
                        content=valid_data['content'],
                        image=image_url,
                        author=request.user
                    )
                    response_serializer = self.get_serializer(blog_post)
                    return Response(response_serializer.data, status=201)
            except Exception as e:
                return Response({'error': str(e)}, status=406)
        else:
            return Response({"error": serializer.errors, "message": "Validation failed"}, status=400)

class UpdateBlogPostApiView(GenericAPIView):
    serializer_class = BlogPostSerializer
    permission_classes = [IsAuthenticated]  

    def put(self, request, *args, **kwargs):
        try:
            blog_post = BlogPost.objects.get(id=kwargs['pk'])

            if blog_post.author != request.user:
                return Response({"error": "You can only update your own blog posts."}, status=status.HTTP_403_FORBIDDEN)

            data = request.data.copy()
            serializer = self.get_serializer(blog_post, data=data, partial=True)

            if serializer.is_valid():
                with transaction.atomic():
                    image_file = request.FILES.get('image')
                    if image_file:
                        uploaded_image = cloudinary_upload(image_file)
                        image_url = uploaded_image.get('secure_url')
                        data['image'] = image_url

                    for field, value in data.items():
                        if value:
                            setattr(blog_post, field, value)

                    blog_post.save()
                    response_serializer = self.get_serializer(blog_post)
                    return Response(response_serializer.data, status=status.HTTP_200_OK)

            return Response({"error": serializer.errors, "message": "Validation failed"}, status=status.HTTP_400_BAD_REQUEST)

        except BlogPost.DoesNotExist:
            return Response({"error": "Blog post not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
class SoftDeleteBlogs(GenericAPIView):
    permission_classes = [IsAuthenticated]  

    def delete(self, request, *args, **kwargs):
        try:
            blog_post = BlogPost.objects.get(id=kwargs['pk'])

            if blog_post.author != request.user:
                return Response({"error": "You can only delete your own blog posts."}, status=status.HTTP_403_FORBIDDEN)

            blog_post.is_deleted = True
            blog_post.save()

            return Response({"message": "Blog post deleted successfully."}, status=status.HTTP_204_NO_CONTENT)

        except BlogPost.DoesNotExist:
            return Response({"error": "Blog post not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        

class GetBlogPostApiView(GenericAPIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        response = {}

        blog_posts = BlogPost.objects.filter(is_deleted=False)

        search_query = request.query_params.get('search', None)
        if search_query:
            blog_posts = blog_posts.filter(
                Q(title__icontains=search_query) | Q(content__icontains=search_query)
            )

        author_name = request.query_params.get('author_name', None)
        if author_name:
            blog_posts = blog_posts.filter(author__username__icontains=author_name)

        date_param = request.query_params.get('date', None)
        if date_param:
            date_object = parse_datetime(date_param)
            if date_object:
                blog_posts = blog_posts.filter(created_at__date=date_object.date())

        sort_order = request.query_params.get('sort', 'asc')
        if sort_order == 'desc':
            blog_posts = blog_posts.order_by('-created_at')
        else:
            blog_posts = blog_posts.order_by('created_at')

        page = int(request.query_params.get('page', 1))  
        page_size = int(request.query_params.get('page_size', 10))  

        offset = (page - 1) * page_size
        limit = offset + page_size

        blog_posts_page = blog_posts[offset:limit]

        blog_data = [
            {
                "id": blog.id,
                "title": blog.title,
                "content": blog.content,
                "image": blog.image.url if blog.image else None,
                "author": blog.author.username,
                "created_at": blog.created_at.isoformat(),
                "modified_at": blog.modified_at.isoformat()
            }
            for blog in blog_posts_page
        ]

        total_count = blog_posts.count()
        num_pages = (total_count + page_size - 1) // page_size 

        response = {
            "message": "Blog posts fetched successfully",
            "status": True,
            "data": {
                "blog_posts": blog_data,
                "pagination": {
                    "count": total_count,
                    "num_pages": num_pages,
                    "current_page": page,
                    "next_page": page + 1 if page < num_pages else None,
                    "previous_page": page - 1 if page > 1 else None
                }
            }
        }

        return Response(response, status=status.HTTP_200_OK)

class AddCommentAPIView(GenericAPIView): 
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, blog_id):
        data = request.data
        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            blog =BlogPost.objects.filter(id=blog_id, is_deleted=False).first()
            if not blog:
                return Response({"message": "Blog not found"}, status=404)

            comment = Comment.objects.create(
                blog=blog,
                name=request.user,
                content=serializer.validated_data['content']
            )

            response = {
                "message": "Comment added successfully",
                "Blog_data" : blog.content,
                "comment": {
                    "user": {
                        "username": comment.name.username,
                        "content": comment.content,
                    },
                    
                    "created_at": comment.created_at
                }
            }

            return Response(response, status=status.HTTP_201_CREATED)
        return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
class MyBlogCommentsAPIView(GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, blog_id):
        try:
            blog = BlogPost.objects.filter(id=blog_id, is_deleted=False, author=request.user).first()
            if not blog:
                return Response({"message": "Blog not found or not authorized"}, status=404)

            comments = Comment.objects.filter(blog=blog).order_by('-created_at')

            response_data = [
                {
                    "user": comment.name.username,
                    "content": comment.content,
                    "created_at": comment.created_at
                }
                for comment in comments
            ]

            return Response({
                "message": "Comments retrieved successfully",
                "blog_title": blog.title,
                "content" : blog.content,
                "comments": response_data
            }, status=200)

        except Exception as e:
            return Response({"error": str(e)}, status=500)
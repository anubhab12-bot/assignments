from django.urls import path
from . import views

urlpatterns = [
    path("sign_up/", views.SignUpApiView.as_view(), name= "User sign up"),
    path("sign_in/", views.SignInApiView.as_view(), name = "User Sign in"),

    path('blogposts/', views.BlogPostApiView.as_view(), name='blogpost-create'),
    path('blogposts/<int:pk>/', views.UpdateBlogPostApiView.as_view(), name='blogpost-update'),
    path('blogposts/<int:pk>/delete/', views.SoftDeleteBlogs.as_view(), name='blogpost-delete'),
    path('get_blogs/', views.GetBlogPostApiView.as_view(), name = "Fetching data"),

    path('blogs/<int:blog_id>/comment/', views.AddCommentAPIView.as_view(), name='add-comment'),

    path('blogs/<int:blog_id>/view-comments/', views.MyBlogCommentsAPIView.as_view(), name='view-blog-comments'),
]
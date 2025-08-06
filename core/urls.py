from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, ProfileViewSet, PostViewSet, CommentViewSet, FollowViewSet
from . import views
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.views import TokenVerifyView


# DRF router will auto-generate routes for each ViewSet
router = DefaultRouter()

router.register(r'users', UserViewSet, basename='user')
router.register(r'profiles', ProfileViewSet, basename='profile')
router.register(r'posts', PostViewSet, basename='post')
router.register(r'comments', CommentViewSet, basename='comment')
router.register(r'follows', FollowViewSet, basename='follow')

urlpatterns = [
    path('', include(router.urls)),#Includes all routes
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('feed/', views.feed_view, name='feed'),
    path('create-post/', views.create_post_view, name='create_post'),
    path('profile/<str:username>/', views.profile_view, name='profile'),
    path('edit_profile/', views.edit_profile_view, name='edit_profile'),
    path('change-password/', views.change_password_view, name='change_password'),
    path('search/', views.search_view, name='search'),
     path('post/<int:pk>/', views.post_detail_view, name='post_detail'),
      path('post/<int:pk>/comment/', views.add_comment_view, name='add_comment'),
      path('posts/<int:post_id>/like/', views.toggle_like_view, name='toggle_like'),
      # JWT login/logout routes
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),  # Login
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("token/verify/", TokenVerifyView.as_view(), name="token_verify"),
]

















"""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.feed_view, name='feed'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/<str:username>/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile_view, name='edit_profile'),
    path('change-password/', views.change_password_view, name='change_password'),
    path('create-post/', views.create_post_view, name='create_post'),
    path('post/<int:post_id>/', views.post_detail_view, name='post_detail'),
    #path('post/<int:post_id>/comment/', views.add_comment_view, name='add_comment'),
    path('search/', views.search_view, name='search'),
    path('follow/<str:username>/', views.follow_user_view, name='follow_user'),
    path('unfollow/<str:username>/', views.unfollow_user_view, name='unfollow_user'),
]
"""
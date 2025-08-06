# Imports for creating API
from rest_framework import viewsets, permissions
from django.contrib.auth.models import User
from .models import Profile, Post, Comment, Follow, Like
from .serializers import UserSerializer,ProfileSerializer,PostSerializer,CommentSerializer,FollowSerializer
from .permissions import IsOwnerOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import AllowAny
from django.views.decorators.http import require_GET
#Imports for creating views that coonsume the API
import requests
import json
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from django.db.models import Q
from django.contrib.auth import authenticate, login, logout
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from .forms import UserRegistrationForm, ProfileForm, LoginForm, PostForm
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseNotAllowed
from .utils import get_auth_headers
from rest_framework.decorators import action

class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

class ProfileViewSet(viewsets.ModelViewSet):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    lookup_field = 'user__username' 

    def get_queryset(self):
        return Profile.objects.select_related('user')
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all().order_by('-created_at')
    serializer_class = PostSerializer
    # Creates permission to allow only users to edit/delete their posts
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    # Filters post by uploader username
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['uploader__username']
    def perform_create(self, serializer):
        serializer.save(uploader=self.request.user)
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def like(self, request, pk=None):
        post = self.get_object()
        post.likes += 1
        post.save()
        return Response({'status': 'post liked', 'likes': post.likes}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def dislike(self, request, pk=None):
        post = self.get_object()
        post.dislikes += 1
        post.save()
        return Response({'status': 'post disliked', 'dislikes': post.dislikes}, status=status.HTTP_200_OK)


class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all().order_by('-created_at')
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    # filter comments by post ID
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['post']  
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class FollowViewSet(viewsets.ModelViewSet):
    queryset = Follow.objects.all()
    serializer_class = FollowSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(follower=self.request.user)



# Views that consume the API
API_BASE_URL = 'http://localhost:8000/api/' 

# View to show the profile page
@login_required

def profile_view(request, username):
        
        headers = get_auth_headers(request)
        if request.method == 'POST':
            # Handle follow action via API
            response = requests.post(f'{API_BASE_URL}profiles/{username}/follow/', headers=headers)
            if response.status_code != 200:
                messages.error(request, 'Failed to follow/unfollow user.')
            return redirect('profile', username=username)
        
        # Get user profile
        profile_response = requests.get(f'{API_BASE_URL}profiles/{username}/', headers=headers)
     
        if profile_response.status_code == 200:
            profile = profile_response.json()
            print("Profile data:", profile)
            print("Profile picture:", profile.get("profile_picture"))  
            # Optionally fetch user's posts
            posts_response = requests.get(f"{API_BASE_URL}posts/?uploader__username={username}", headers=headers)
            posts = posts_response.json().get("results", []) if posts_response.status_code == 200 else []

            return render(request, 'profile.html', {
                'profile': profile,
                'posts': posts
            })

        return render(request, 'profile.html', {'error': 'Profile not found'})

# View for post details
def post_detail_view(request, pk):
    token = request.session.get('access_token')
    headers = {'Authorization': f'Bearer {token}'} if token else {}

    # Fetch post
    post_response = requests.get(f"{API_BASE_URL}posts/{pk}/", headers=headers)
    if post_response.status_code != 200:
        messages.error(request, "Post not found or failed to load.")
        return redirect("feed")  # redirect to feed or 404 page

    post = post_response.json()

    # Fetch comments
    try:
        response = requests.get(f"{API_BASE_URL}comments/?post={pk}", headers=headers)
        if response.status_code == 200:
            comment_data = response.json()
            comments = comment_data.get("results", [])
            print('COMMENTS FOR DEBUDDING', comments)
        else:
            comments = []
            messages.error(request, "Failed to fetch comments.")
    except requests.RequestException:
        comments = []
        messages.error(request, "Network error while fetching comments.")

    return render(request, "post_detail.html", {
        "post": post,
        "comments": comments
    })


# view for adding comment
@login_required
def add_comment_view(request, pk):
    if request.method == "POST":
        token = request.session.get('access_token')
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
        }

        comment_content = request.POST.get("content")
        payload = {'content': comment_content,
                    'post': pk}

        url = f"{API_BASE_URL}comments/"  # Make sure this matches your API URL
        response = requests.post(url, json=payload, headers=headers)

        # Print the status code and response for debugging
        print("STATUS:", response.status_code)
        print("RESPONSE:", response.text)

        if response.status_code == 201:
            return redirect("post_detail", pk=pk)
        else:
            messages.error(request, "Failed to post comment.")

    return redirect("post_detail", pk=pk)

# View for editing profile
@login_required
def edit_profile_view(request):
    headers = get_auth_headers(request)  # Handles token refresh or redirect

    if request.method == 'POST':
        bio = request.POST.get('bio')
        profile_image = request.FILES.get('profile_image')

        data = {'bio': bio}
        files = {'profile_image': profile_image} if profile_image else {}

        response = requests.put(
            f'{API_BASE_URL}profiles/{request.user.username}/',
            data=data,
            files=files,
            headers=headers
        )

        if response.status_code in [200, 204]:
            messages.success(request, 'Profile updated successfully.')
            return redirect('profile', username=request.user.username)
        else:
            messages.error(request, 'Failed to update profile.')

    # GET request to show current data in form
    response = requests.get(f'{API_BASE_URL}profiles/{request.user.username}/', headers=headers)

    if response.status_code == 200:
        profile = response.json()
    else:
        messages.error(request, 'Failed to load profile.')

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES)
        if form.is_valid():
            bio = form.cleaned_data.get('bio')
            profile_image = form.cleaned_data.get('profile_image')

            data = {'bio': bio}
            files = {'profile_image': profile_image} if profile_image else {}

            update_response = requests.put(
                f'{API_BASE_URL}profiles/{request.user.username}/',
                data=data,
                files=files,
                headers=headers
            )

            if update_response.status_code in [200, 204]:
                messages.success(request, 'Profile updated successfully.')
                return redirect('profile', username=request.user.username)
            else:
                messages.error(request, 'Failed to update profile.')
    else:
        # Pre-fill the form using API response
        form = ProfileForm(initial={
            'bio': profile.get('bio', '')
        })

    return render(request, 'edit_profile.html', {
        'form': form,
        'profile': profile
    })

# View for changing password
@login_required
def change_password_view(request):
    if request.method == 'POST':
        current_pw = request.POST.get('current_password')
        new_pw = request.POST.get('new_password')
        confirm_pw = request.POST.get('confirm_password')

        if new_pw != confirm_pw:
            messages.error(request, "New passwords do not match.")
        elif not request.user.check_password(current_pw):
            messages.error(request, "Incorrect current password.")
        else:
            request.user.set_password(new_pw)
            request.user.save()
            update_session_auth_hash(request, request.user)
            messages.success(request, "Password updated successfully.")
            return redirect('profile', username=request.user.username)

    return render(request, 'change_password.html')


# View for searching users
def search_view(request):
    query = request.GET.get('q')
    users = User.objects.filter(Q(username__icontains=query) | Q(profile__bio__icontains=query)) if query else []
    return render(request, 'search_results.html', {'query': query, 'users': users})



# View for showing feed
@login_required
def feed_view(request):
    token = request.session.get('access_token')  # JWT token if stored
    headers = {'Authorization': f'Bearer {token}'} if token else {}

    response = requests.get(f'{API_BASE_URL}posts/', headers=headers)
    if response.status_code == 200:
        data = response.json()
        posts = data.get('results', [])  # Only pass the list of posts
    else:
        posts = []

    return render(request, 'feed.html', {'posts': posts})
# View for creating posts
@login_required
def create_post_view(request):
    token = request.session.get('access_token')  # JWT token
    headers = {'Authorization': f'Bearer {token}'} if token else {}

    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)

        if form.is_valid():
            caption = form.cleaned_data['caption']
            image = form.cleaned_data.get('image')

            data = {'caption': caption}
            files = {'image': image} if image else {}

            response = requests.post(f'{API_BASE_URL}posts/', data=data, files=files, headers=headers)

            if response.status_code in [200, 201]:
                return redirect('feed')
            else:
                error = response.json()
                return render(request, 'create-post.html', {'form': form, 'error': error})

    else:
        form = PostForm()

    return render(request, 'create-post.html', {'form': form})


def register_view(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        profile_form = ProfileForm(request.POST, request.FILES)

        if form.is_valid() and profile_form.is_valid():
            user = form.save()
            messages.success(request, 'Registration successful. You can now log in.')
            return redirect('login')
    else:
        form = UserRegistrationForm()
        profile_form = ProfileForm()

    return render(request, 'register.html', {'form': form, 'profile_form': profile_form})

# View for login
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from .forms import LoginForm
from rest_framework_simplejwt.tokens import RefreshToken

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)

        if form.is_valid():
            user = form.cleaned_data['user']
            login(request, user)

            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)

            # Store tokens in session
            request.session['access_token'] = access_token
            request.session['refresh_token'] = refresh_token

            messages.success(request, f"Welcome back, {user.username}!")
            return redirect('feed')
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = LoginForm()

    return render(request, 'login.html', {'form': form})



# View for logout
def blacklist_token(token):
    try:
        token.blacklist()
    except Exception:
        pass

@login_required
def logout_view(request):
    refresh_token = request.session.get('refresh_token')
    if refresh_token:
        token = RefreshToken(refresh_token)
        blacklist_token(token)  # blacklist refresh token

    logout(request)
    request.session.flush()
    messages.success(request, "Logged out successfully.")
    return redirect('login')

def toggle_like_view(request, post_id):
    headers = get_auth_headers(request)

    if request.method == 'POST':
        response = requests.post(
            f'{API_BASE_URL}posts/{post_id}/like/',
            headers=headers
        )

        if response.status_code == 200:
            messages.success(request, 'Liked successfully.')
        elif response.status_code == 401:
            messages.error(request, 'Login again. Session expired.')
        else:
            messages.error(request, 'Failed to like the post.')

    return redirect(request.META.get('HTTP_REFERER', '/'))











"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from .forms import UserRegistrationForm, LoginForm, ProfileForm, PostForm, CommentForm, SearchForm, PasswordChangeForm
from django.contrib import messages
from .models import  Post, Comment, Follow
from django.contrib.auth import update_session_auth_hash

# registration view
def register_view(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Account created successfully! You can now log in.')
            return redirect('login')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = UserRegistrationForm()
    
    return render(request, 'registration/register.html', {'form': form})


# login view
def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data['user']
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            return redirect('feed')  
    else:
        form = LoginForm()

    return render(request, 'registration/login.html', {'form': form})


# Logout view
@login_required
def logout_view(request):
    logout(request)
    return redirect('login')


# View for feed
def feed_view(request):
    posts = Post.objects.all().order_by('-created_at')  # Recent posts first
    return render(request, 'social/feed.html', {'posts': posts})


# View for profile
@login_required
def profile_view(request, username):
    user_profile = get_object_or_404(User, username=username)
    posts = Post.objects.filter(author=user_profile).order_by('-created_at')
    is_following = Follow.objects.filter(follower=request.user, following=user_profile).exists()

    return render(request, 'profile/profile.html', {
        'user_profile': user_profile,
        'posts': posts,
        'is_following': is_following
    })



# view for updating profile
@login_required
def edit_profile_view(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=request.user.profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('profile', username=request.user.username)
        else:
            messages.error(request, "Error updating your profile.")
    else:
        form = ProfileForm(instance=request.user.profile)
    return render(request, 'profile/edit_profile.html', {'form': form})

# View for changing password
@login_required
def change_password_view(request):
    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  
            messages.success(request, "Your password has been changed successfully.")
            return redirect('profile', username=request.user.username)
        else:
            messages.error(request, "Please correct the error below.")
    else:
        form = PasswordChangeForm(user=request.user)
    return render(request, 'auth/change_password.html', {'form': form})

# View for creating a post
@login_required
def create_post_view(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            messages.success(request, "Post created successfully.")
            return redirect('feed')
        else:
            messages.error(request, "Failed to create post.")
    else:
        form = PostForm()
    return render(request, 'posts/create_post.html', {'form': form})


# View for viewing and commenting on post
@login_required
def post_detail_view(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    comments = Comment.objects.filter(post=post).order_by('-created_at')

    if request.method == 'POST':
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.user = request.user
            comment.post = post
            comment.save()
            messages.success(request, "Comment added.")
            return redirect('post_detail', post_id=post_id)
        else:
            messages.error(request, "Failed to add comment.")
    else:
        comment_form = CommentForm()

    return render(request, 'posts/post_detail.html', {
        'post': post,
        'comments': comments,
        'comment_form': comment_form
    })

# View for searching users and posts
@login_required
def search_view(request):
    query = request.GET.get('query', '')
    users = posts = []
    if query:
        users = User.objects.filter(username__icontains=query)
        posts = Post.objects.filter(caption__icontains=query)
    form = SearchForm(initial={'query': query})
    return render(request, 'search/search.html', {
        'form': form,
        'users': users,
        'posts': posts,
        'query': query
    })


# View for following user
@login_required
def follow_user_view(request, username):
    user_to_follow = get_object_or_404(User, username=username)
    if user_to_follow != request.user:
        Follow.objects.get_or_create(follower=request.user, following=user_to_follow)
        messages.success(request, f'You are now following {user_to_follow.username}.')
    else:
        messages.warning(request, 'You cannot follow yourself.')
    return redirect('profile', username=user_to_follow.username)


# View for unfollowing user
@login_required
def unfollow_user_view(request, username):
    user_to_unfollow = get_object_or_404(User, username=username)
    if user_to_unfollow != request.user:
        Follow.objects.filter(follower=request.user, following=user_to_unfollow).delete()
        messages.success(request, f'You have unfollowed {user_to_unfollow.username}.')
    else:
        messages.warning(request, 'You cannot unfollow yourself.')
    return redirect('profile', username=user_to_unfollow.username)
"""
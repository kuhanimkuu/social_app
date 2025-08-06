from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Post, Comment, Follow

# Create your tests here.
class BaseTestCase(APITestCase):
    def setUp(self):
        # Create two users for testing
        self.user1 = User.objects.create_user(username='user1', password='pass1234')
        self.user2 = User.objects.create_user(username='user2', password='pass5678')

        # Generate JWT tokens for both users to authenticate API requests
        self.token1 = str(RefreshToken.for_user(self.user1).access_token)
        self.token2 = str(RefreshToken.for_user(self.user2).access_token)

        # Set the authorization header with user1's token by default
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token1}")
    
    # Test case for user registration endpoint
    def test_user_registration(self):
        url = '/api/register/' # This is the endpoint to register new users
        data = {
            'username': 'newuser',
            'password': 'newpass123',
            'password2': 'newpass123',  # Confirm password field
            'email': 'newuser@example.com'
        }
        response = self.client.post(url, data)
        # confirm that registration was successful (HTTP 201 Created)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # confirm that the new user exists in the database
        self.assertTrue(User.objects.filter(username='newuser').exists())

    # Test case for user login and obtaining JWT token
    def test_user_login_and_get_token(self):
        url = '/api/token/'  # JWT token obtain endpoint
        data = {
            'username': 'user1',
            'password': 'pass1234',
        }
        response = self.client.post(url, data)
        # confirm login success (HTTP 200 OK)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # confirm the response contains 'access' and 'refresh' tokens
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    # Test case for creating a new post
    def test_create_post(self):
        url = '/api/posts/'
        data = {
            'caption': 'My first post',
            'image': r'C:\Users\Administrator\Desktop\photos\WhatsApp Image 2025-04-19 at 18.06.57_0f26c2d5.jpg'
        }
        response = self.client.post(url, data)
        # confirm that the post was created successfully
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # confirm that the post count in DB is 1
        self.assertEqual(Post.objects.count(), 1)
        # confirm the post caption matches what we sent
        self.assertEqual(Post.objects.first().caption, 'My first post')

    # Test case for retrieving the list of posts (paginated)
    def test_get_post_list(self):
        # Create a post to test the retrieval
        Post.objects.create(uploader=self.user1, caption='Hello World')
        url = '/api/posts/'
        response = self.client.get(url)
        # confirm the request was successful
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # confirm at least one post is returned in paginated results
        self.assertTrue(len(response.data['results']) >= 1)

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from cloudinary.models import CloudinaryField
# Create your models here.

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE) #one profile per user
    profile_picture = CloudinaryField('image', default='default_profile_image')# Cloudinary-hosted profile image
    bio = models.TextField(blank=True, null=True)  # Optional bio field
    age = models.PositiveIntegerField(blank=True, null=True)  # Optional age field
    created_at = models.DateTimeField(auto_now_add=True)  # Timestamp when profile was created

    def __str__(self):
        return f"{self.user.username}'s Profile"

# Model for post
class Post(models.Model):
    uploader = models.ForeignKey(User,on_delete=models.CASCADE, related_name='posts') # Author of the post
    image = CloudinaryField('image', blank=True, null=True) # image to a post
    caption = models.TextField() # Caption text on a post
    created_at = models.DateTimeField(auto_now_add=True) # Timestamp for creation of post
    updated_at = models.DateTimeField(auto_now=True) # Timestamp of last update

    def __str__(self):
        return f"{self.uploader.username}'s Post - {self.created_at.strftime('%Y-%m-%d')}"
    

# Comment model to a post
class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE) # author of comment
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comment') # Associated post to the comment
    content = models.TextField() # content of the comment
    created_at = models.DateTimeField(auto_now_add=True) #Timestamp for creation of comment
    likes = models.ManyToManyField(User, related_name='liked_photos', blank=True)
    dislikes = models.ManyToManyField(User, related_name='disliked_photos', blank=True)

    def total_likes(self):
            return self.likes.count()
        
    def total_dislikes(self):
            return self.dislikes.count()
    def __str__(self):
        return  f"Comment by {self.user.username} on Post {self.post.id}"

# Like model
class Like(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Who liked the post
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')  # Which post was liked
    created_at = models.DateTimeField(auto_now_add=True)  # When the like was made

    class Meta:
        unique_together = ('user', 'post')  # Prevent duplicate likes on the same post by the same user

    def __str__(self):
        return f"{self.user.username} liked Post {self.post.id}"

# Follow model- used for user following another user
class Follow(models.Model):
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers')
    followed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('follower', 'following')  # Prevent duplicate follows

    def __str__(self):
        return f"{self.follower.username} follows {self.following.username}"
    


from django import forms
from django.contrib.auth.models import User
from .models import Profile, Comment, Post
from django.contrib.auth.hashers import make_password
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import PasswordChangeForm
#Form for user registration
class UserRegistrationForm(forms.ModelForm):
    password=forms.CharField(widget=forms.PasswordInput) #Hashes(hides characters of password for enhanced security )
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput)
    email = forms.EmailField(required=True)
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2'] 
    #Custom made validation to ensure both passwords match
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password2 = cleaned_data.get('password2')
        # If the passwords don't match, raise an error on password2 field
        if password and password2 and password != password2:
            self.add_error('password2',"Passwords don't match")
        return cleaned_data
    
    # Override the save method to hash the password before saving the user
    def save(self, commit=True):
        user = super().save(commit=False) #It creates a User object but doesn't save it to the database yet
        user.password = make_password(self.cleaned_data['password']) # This securely hashes the password

        if commit:
            user.save()
            return user
#Login form
class LoginForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')

        # Authenticating the user using djangos builtin method
        user = authenticate(username=username, password=password)

        if not user:
            raise forms.ValidationError("Invalid username or password")

        cleaned_data['user'] = user  # Store user for use in view
        return cleaned_data

#Profile update form
class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['bio', 'profile_picture']


# Form for posting
class PostForm(forms.ModelForm):
    caption = forms.CharField(
        label="What's on your mind?",
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Write your caption here...'}),
        required=False
    )
    
    image = forms.ImageField(label='Upload an Image')

    class Meta:
        model = Post
        fields = ['caption', 'image']  # Fields to show in the form

    #Custom validation for image type or size could go here
    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image and image.size > 5 * 1024 * 1024:  # limit: 5MB
            raise forms.ValidationError("Image size should not exceed 5MB.")
        return image
    
#Form for comment
class CommentForm(forms.ModelForm):
    content = forms.CharField(
        label='Add a comment...',
        widget=forms.Textarea(attrs={'rows': 2, 'placeholder': 'Write your comment'}),
    )

    class Meta:
        model = Comment
        fields = ['content']  


# Form for searching
class SearchForm(forms.Form):
    query = forms.CharField(
        label='Search',
        max_length=100,
        widget=forms.TextInput(attrs={'placeholder': 'Search users or posts'})
    )

#Paasword change form
class PasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(
        label='Current Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter current password'})
    )
    new_password1 = forms.CharField(
        label='New Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter new password'})
    )
    new_password2 = forms.CharField(
        label='Confirm New Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm new password'})
    )
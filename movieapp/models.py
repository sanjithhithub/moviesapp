from django.db import models

from django.db import models

class MoviePost(models.Model):
    post_no = models.PositiveIntegerField(unique=True, editable=False)
    movie_name = models.CharField(max_length=200)
    image = models.ImageField(upload_to='moviepage/', blank=True, null=True)
    movie_link = models.URLField(blank=True, null=True)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.post_no:
            last_post = MoviePost.objects.order_by('-post_no').first()
            self.post_no = 1 if not last_post else last_post.post_no + 1
        super().save(*args, **kwargs)

class MovieAnalytics(models.Model):
    movie = models.OneToOneField(
        MoviePost,
        on_delete=models.CASCADE,
        related_name="analytics"
    )
    view_count = models.PositiveIntegerField(default=0)
    last_viewed = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.movie.movie_name} analytics"


# movieapp/models.py
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

class AdminUserManager(BaseUserManager):
    def create_user(self, username, password=None):
        if not username:
            raise ValueError("Admin user must have a username")
        user = self.model(username=username)
        user.set_password(password)
        user.is_active = True
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None):
        user = self.create_user(username=username, password=password)
        user.is_superuser = True
        user.is_staff = True
        user.save(using=self._db)
        return user

class AdminUser(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=50, unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=True)

    objects = AdminUserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.username

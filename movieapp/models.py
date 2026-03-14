from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

# ============================================================
# ADMIN USER MANAGER
# ============================================================

class AdminUserManager(BaseUserManager):
    def create_user(self, username, password=None, role="subadmin"):
        if not username:
            raise ValueError("Username is required")

        user = self.model(
            username=username,
            role=role
        )

        user.set_password(password)
        user.is_active = True
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password):
        user = self.create_user(
            username=username,
            password=password,
            role="admin"
        )
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


# ============================================================
# ADMIN USER MODEL
# ============================================================

class AdminUser(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = (
        ("admin", "Main Admin"),
        ("subadmin", "Sub Admin"),
    )

    username = models.CharField(
        max_length=50,
        unique=True
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES
    )

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = AdminUserManager()

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = []

    def __str__(self):
        return f"{self.username} - {self.role}"


# ============================================================
# MOVIE POST MODEL
# ============================================================

class MoviePost(models.Model):
    post_no = models.PositiveIntegerField(
        unique=True,
        db_index=True
    )

    movie_name = models.CharField(max_length=200)

    # Because of our STORAGES settings, this ImageField will 
    # automatically upload to Cloudinary under the 'moviepage/' folder.
    image = models.ImageField(
        upload_to="moviepage/",
        blank=True,
        null=True
    )

    movie_link = models.URLField(
        blank=True,
        null=True
    )

    description = models.TextField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"post_no:{self.post_no} - {self.movie_name}"


# ============================================================
# MOVIE ANALYTICS
# ============================================================

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
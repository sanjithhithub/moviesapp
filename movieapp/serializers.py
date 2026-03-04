from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


from rest_framework import serializers
from .models import MoviePost, MovieAnalytics

class PublicMoviePostSerializer(serializers.ModelSerializer):
    class Meta:
        model = MoviePost
        fields = [
            "post_no",
            "movie_name",
            "image",
            "movie_link",
            "description",
            "created_at",
        ]
        
class AdminMoviePostSerializer(serializers.ModelSerializer):
    class Meta:
        model = MoviePost
        fields = "__all__"
        read_only_fields = [
            "post_no",
            "created_at",
            "view_count",
        ]
        
        read_only_fields = ["post_no", "created_at"]

class MovieAnalyticsSerializer(serializers.ModelSerializer):
    movie_name = serializers.CharField(source="movie.movie_name", read_only=True)
    post_no = serializers.IntegerField(source="movie.post_no", read_only=True)

    class Meta:
        model = MovieAnalytics
        fields = [
            "post_no",
            "movie_name",
            "view_count",
            "last_viewed",
        ]

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


# 👑 MAIN ADMIN LOGIN
class MainAdminTokenSerializer(TokenObtainPairSerializer):

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom fields inside JWT
        token["username"] = user.username
        token["role"] = user.role

        return token

    def validate(self, attrs):
        data = super().validate(attrs)

        # Block inactive users
        if not self.user.is_active:
            raise serializers.ValidationError("Account is inactive")

        # Allow only main admin
        if self.user.role != "admin":
            raise serializers.ValidationError(
                "Only main admin can login here"
            )

        # Extra response data
        data["username"] = self.user.username
        data["role"] = self.user.role

        return data


# 👨‍💼 SUB ADMIN LOGIN
class SubAdminTokenSerializer(TokenObtainPairSerializer):

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom fields inside JWT
        token["username"] = user.username
        token["role"] = user.role

        return token

    def validate(self, attrs):
        data = super().validate(attrs)

        # Block inactive users
        if not self.user.is_active:
            raise serializers.ValidationError("Account is inactive")

        # Allow only sub admin
        if self.user.role != "subadmin":
            raise serializers.ValidationError(
                "Only sub admin can login here"
            )

        data["username"] = self.user.username
        data["role"] = self.user.role

        return data
    
    
# serializers.py

from rest_framework import serializers
from .models import AdminUser


class CreateAdminSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = AdminUser
        fields = ['username', 'password', 'role']

    def create(self, validated_data):
        return AdminUser.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            role=validated_data['role']
        )
        
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class AdminLoginSerializer(TokenObtainPairSerializer):

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        token['role'] = user.role
        token['username'] = user.username

        return token        
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import MoviePost, MovieAnalytics, AdminUser


# ============================================================
# PUBLIC MOVIE SERIALIZER
# ============================================================

class PublicMoviePostSerializer(serializers.ModelSerializer):

    class Meta:
        model = MoviePost
        fields = "__all__"


# ============================================================
# ADMIN MOVIE SERIALIZER
# ============================================================

class AdminMoviePostSerializer(serializers.ModelSerializer):

    # ✅ FIX: Clear auto UniqueValidator DRF adds because of unique=True on model.
    # Without validators=[], update always fails with "post_no already exists"
    # even when updating the same record.
    post_no = serializers.IntegerField(validators=[])

    class Meta:
        model = MoviePost
        fields = "__all__"
        read_only_fields = ["created_at"]
        extra_kwargs = {
            "image":       {"required": False, "allow_null": True},
            "description": {"required": False, "allow_null": True},
            "movie_link":  {"required": False, "allow_null": True},
        }

    def validate_post_no(self, value):

        # Get current instance pk on update, None on create
        current_pk = self.instance.pk if self.instance else None

        # Block only if a DIFFERENT record already owns this post_no
        if MoviePost.objects.filter(post_no=value).exclude(pk=current_pk).exists():
            raise serializers.ValidationError("Post number already exists.")

        return value

    def update(self, instance, validated_data):
        # Preserve existing image if not re-sent in the request
        if "image" not in validated_data:
            validated_data["image"] = instance.image
        return super().update(instance, validated_data)


# ============================================================
# ANALYTICS SERIALIZER
# ============================================================

class MovieAnalyticsSerializer(serializers.ModelSerializer):

    movie_name = serializers.CharField(
        source="movie.movie_name",
        read_only=True
    )

    post_no = serializers.IntegerField(
        source="movie.post_no",
        read_only=True
    )

    class Meta:
        model = MovieAnalytics
        fields = ["post_no", "movie_name", "view_count", "last_viewed"]


# ============================================================
# CREATE ADMIN
# ============================================================

class CreateAdminSerializer(serializers.ModelSerializer):

    password = serializers.CharField(write_only=True)

    class Meta:
        model = AdminUser
        fields = ["username", "password", "role"]

    def create(self, validated_data):
        return AdminUser.objects.create_user(
            username=validated_data["username"],
            password=validated_data["password"],
            role=validated_data["role"]
        )


# ============================================================
# LOGIN SERIALIZER
# ============================================================

class AdminLoginSerializer(TokenObtainPairSerializer):

    role = serializers.ChoiceField(choices=["admin", "subadmin"])

    def validate(self, attrs):

        role = attrs.get("role")
        data = super().validate(attrs)

        if self.user.role != role:
            raise serializers.ValidationError(
                {"role": "Selected role does not match user role"}
            )

        data["username"] = self.user.username
        data["role"] = self.user.role

        return data
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import MoviePost, MovieAnalytics, AdminUser

# ============================================================
# PUBLIC MOVIE SERIALIZER
# ============================================================

class PublicMoviePostSerializer(serializers.ModelSerializer):
    # This ensures the frontend gets the full https:// URL from Cloudinary
    image = serializers.SerializerMethodField()

    class Meta:
        model = MoviePost
        fields = "__all__"

    def get_image(self, obj):
        if obj.image:
            return obj.image.url
        return None


# ============================================================
# ADMIN MOVIE SERIALIZER
# ============================================================

class AdminMoviePostSerializer(serializers.ModelSerializer):
    # ✅ FIX: Clear auto UniqueValidator to allow updates
    post_no = serializers.IntegerField(validators=[])
    
    # Return absolute Cloudinary URL
    image_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = MoviePost
        fields = "__all__"
        read_only_fields = ["created_at"]
        extra_kwargs = {
            "image":       {"required": False, "allow_null": True},
            "description": {"required": False, "allow_null": True},
            "movie_link":  {"required": False, "allow_null": True},
        }

    def get_image_url(self, obj):
        return obj.image.url if obj.image else None

    def validate_post_no(self, value):
        current_pk = self.instance.pk if self.instance else None
        if MoviePost.objects.filter(post_no=value).exclude(pk=current_pk).exists():
            raise serializers.ValidationError("Post number already exists.")
        return value

    def update(self, instance, validated_data):
        # Only overwrite image if a new one is uploaded
        if "image" not in validated_data:
            validated_data["image"] = instance.image
        return super().update(instance, validated_data)


# ============================================================
# ANALYTICS SERIALIZER
# ============================================================

class MovieAnalyticsSerializer(serializers.ModelSerializer):
    movie_name = serializers.CharField(source="movie.movie_name", read_only=True)
    post_no = serializers.IntegerField(source="movie.post_no", read_only=True)

    class Meta:
        model = MovieAnalytics
        fields = ["post_no", "movie_name", "view_count", "last_viewed"]


# ============================================================
# CREATE ADMIN SERIALIZER
# ============================================================

class CreateAdminSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = AdminUser
        fields = ["username", "password", "role"]

    def create(self, validated_data):
        return AdminUser.objects.create_user(**validated_data)


# ============================================================
# LOGIN SERIALIZER
# ============================================================

class AdminLoginSerializer(TokenObtainPairSerializer):
    role = serializers.ChoiceField(choices=["admin", "subadmin"])

    def validate(self, attrs):
        # Check role before generating the token
        username = attrs.get(self.username_field)
        role_input = attrs.get("role")
        
        try:
            user = AdminUser.objects.get(username=username)
            if user.role != role_input:
                raise serializers.ValidationError({"role": "Incorrect role for this user."})
        except AdminUser.DoesNotExist:
            # Let the super().validate handle the "User not found" error correctly
            pass

        data = super().validate(attrs)

        # Add custom claims to the response
        data["username"] = self.user.username
        data["role"] = self.user.role

        return data
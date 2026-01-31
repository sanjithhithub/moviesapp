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



class AdminTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)

        # extra response fields (optional)
        data['username'] = self.user.username
        data['is_admin'] = self.user.is_staff

        return data

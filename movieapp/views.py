from rest_framework import viewsets, permissions
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from django.db.models import F

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import MoviePost, MovieAnalytics
from .serializers import (
    AdminMoviePostSerializer,
    PublicMoviePostSerializer,
    AdminTokenObtainPairSerializer,
    MovieAnalyticsSerializer,
)
from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from django.db.models import Sum
from .models import MoviePost, MovieAnalytics



class AdminMovieViewSet(viewsets.ModelViewSet):
    queryset = MoviePost.objects.all()
    serializer_class = AdminMoviePostSerializer
    permission_classes = [permissions.IsAdminUser]
    lookup_field = "post_no"

    http_method_names = ["get", "post", "put", "delete", "options"]

    @swagger_auto_schema(
        operation_summary="Admin – List all movies",
        operation_description="Admin can view all movies including analytics",
        responses={200: AdminMoviePostSerializer(many=True)},
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Admin – Create movie",
        request_body=AdminMoviePostSerializer,
        responses={201: AdminMoviePostSerializer},
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Admin – Update movie by post_no",
        manual_parameters=[
            openapi.Parameter(
                "post_no",
                openapi.IN_PATH,
                type=openapi.TYPE_INTEGER,
                required=True,
            )
        ],
        request_body=AdminMoviePostSerializer,
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Admin – Delete movie by post_no",
        manual_parameters=[
            openapi.Parameter(
                "post_no",
                openapi.IN_PATH,
                type=openapi.TYPE_INTEGER,
                required=True,
            )
        ],
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

# 🌍 Public APIs
class PublicMovieList(ListAPIView):
    queryset = MoviePost.objects.all()
    serializer_class = PublicMoviePostSerializer

    @swagger_auto_schema(
        operation_summary="Public – List movies",
        operation_description="Get all movies (analytics hidden)",
        responses={200: PublicMoviePostSerializer(many=True)},
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

class PublicMovieDetail(RetrieveAPIView):
    queryset = MoviePost.objects.all()
    serializer_class = PublicMoviePostSerializer
    lookup_field = "post_no"

    @swagger_auto_schema(
        operation_summary="Public – Get movie by post number",
        operation_description="Retrieve movie and increment view count",
        manual_parameters=[
            openapi.Parameter(
                "post_no",
                openapi.IN_PATH,
                type=openapi.TYPE_INTEGER,
                required=True,
            )
        ],
        responses={200: PublicMoviePostSerializer},
    )
    def get(self, request, *args, **kwargs):
        movie = self.get_object()

        analytics, _ = MovieAnalytics.objects.get_or_create(movie=movie)
        analytics.view_count = F("view_count") + 1
        analytics.save(update_fields=["view_count"])

        analytics.refresh_from_db()

        serializer = self.get_serializer(movie)
        return Response(serializer.data)


class AdminAnalyticsView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        analytics = MovieAnalytics.objects.select_related("movie")

        data = []
        for item in analytics:
            data.append({
                "post_no": item.movie.post_no,
                "movie_name": item.movie.movie_name,
                "view_count": item.view_count,
                "last_viewed": item.last_viewed,
            })

        total_views = analytics.aggregate(
            total=Sum("view_count")
        )["total"] or 0

        return Response({
            "total_movies": analytics.count(),
            "total_views": total_views,
            "movies": data
        })

    
# 🔑 Admin JWT Token
class AdminTokenView(TokenObtainPairView):
    serializer_class = AdminTokenObtainPairSerializer

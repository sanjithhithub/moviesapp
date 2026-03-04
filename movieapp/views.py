from rest_framework import viewsets, permissions, status
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.parsers import MultiPartParser, FormParser
from django.db.models import F, Sum

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import MoviePost, MovieAnalytics
from .serializers import (
    AdminMoviePostSerializer,
    PublicMoviePostSerializer,
    MainAdminTokenSerializer,
    SubAdminTokenSerializer,
    CreateAdminSerializer,
)

# ============================================================
# 🔐 CREATE ADMIN ACCOUNT
# ============================================================

class CreateAdminView(APIView):

    @swagger_auto_schema(
        operation_summary="Create Main Admin / Sub Admin",
        request_body=CreateAdminSerializer,
    )
    def post(self, request):
        serializer = CreateAdminSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(
                {"success": True, "message": "Account created successfully"},
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ============================================================
# 🔐 LOGIN APIs
# ============================================================

class MainAdminLoginView(TokenObtainPairView):
    serializer_class = MainAdminTokenSerializer


class SubAdminLoginView(TokenObtainPairView):
    serializer_class = SubAdminTokenSerializer


# ============================================================
# 🎬 MOVIE PERMISSION (ROLE BASED)
# ============================================================

class MoviePermission(permissions.BasePermission):

    def has_permission(self, request, view):

        if not request.user or not request.user.is_authenticated:
            return False

        # Full access roles
        if request.user.role in ["admin", "mainadmin"]:
            return True

        # Subadmin → only POST allowed
        if request.user.role == "subadmin":
            return request.method == "POST"

        return False


# ============================================================
# 🎬 ADMIN MOVIE VIEWSET
# ============================================================

class AdminMovieViewSet(viewsets.ModelViewSet):
    queryset = MoviePost.objects.all()
    serializer_class = AdminMoviePostSerializer
    permission_classes = [IsAuthenticated, MoviePermission]
    lookup_field = "post_no"
    parser_classes = (MultiPartParser, FormParser)

    http_method_names = ["get", "post", "put", "patch", "delete", "options"]

    @swagger_auto_schema(
        operation_summary="Admin – Create Movie",
        request_body=AdminMoviePostSerializer,
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)


# ============================================================
# 🌍 PUBLIC MOVIE APIs (NO TOKEN REQUIRED)
# ============================================================

class PublicMovieList(ListAPIView):
    queryset = MoviePost.objects.all()
    serializer_class = PublicMoviePostSerializer
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary="Public – List Movies",
        responses={200: PublicMoviePostSerializer(many=True)},
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class PublicMovieDetail(RetrieveAPIView):
    queryset = MoviePost.objects.all()
    serializer_class = PublicMoviePostSerializer
    lookup_field = "post_no"
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary="Public – Get Movie & Increase View Count",
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


# ============================================================
# 📊 ADMIN ANALYTICS API
# ============================================================

class AdminAnalyticsView(APIView):
    permission_classes = [IsAuthenticated, MoviePermission]

    @swagger_auto_schema(
        operation_summary="Admin – View Movie Analytics",
    )
    def get(self, request):

        analytics = MovieAnalytics.objects.select_related("movie")

        data = [
            {
                "post_no": item.movie.post_no,
                "movie_name": item.movie.movie_name,
                "view_count": item.view_count,
                "last_viewed": item.last_viewed,
            }
            for item in analytics
        ]

        total_views = analytics.aggregate(total=Sum("view_count"))["total"] or 0

        return Response({
            "total_movies": analytics.count(),
            "total_views": total_views,
            "movies": data
        })
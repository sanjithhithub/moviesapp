from rest_framework import viewsets, status
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authentication import BasicAuthentication
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.views import TokenObtainPairView

from django.db.models import F, Sum

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import MoviePost, MovieAnalytics
from .serializers import (
    AdminMoviePostSerializer,
    PublicMoviePostSerializer,
    AdminLoginSerializer,
    CreateAdminSerializer,
)

from .pagination import MoviePagination


# ============================================================
# CREATE ADMIN
# ============================================================

class CreateAdminView(APIView):

    @swagger_auto_schema(request_body=CreateAdminSerializer)
    def post(self, request):

        serializer = CreateAdminSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Account created"},
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ============================================================
# LOGIN
# ============================================================

class AdminLoginView(TokenObtainPairView):
    serializer_class = AdminLoginSerializer


# ============================================================
# ADMIN MOVIE CRUD
# ============================================================

class AdminMovieViewSet(viewsets.ModelViewSet):

    queryset = MoviePost.objects.all().order_by("-created_at")
    serializer_class = AdminMoviePostSerializer

    # ✅ Admin views explicitly require JWT + login
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    parser_classes = (MultiPartParser, FormParser)
    pagination_class = MoviePagination
    lookup_field = "pk"

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()

        serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=partial
        )

        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, "_prefetched_objects_cache", None):
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response(
            {"message": "Deleted successfully"},
            status=status.HTTP_204_NO_CONTENT
        )


# ============================================================
# PUBLIC MOVIE LIST — no token, no auth, just data + pagination
# ============================================================

class PublicMovieList(ListAPIView):

    queryset = MoviePost.objects.all().order_by("-created_at")
    serializer_class = PublicMoviePostSerializer
    pagination_class = MoviePagination

    # ✅ Completely open — no authentication, no permission check
    authentication_classes = []
    permission_classes = [AllowAny]


# ============================================================
# PUBLIC MOVIE DETAIL — no token, search by ?search=postnumber1
# ============================================================

class PublicMovieDetail(APIView):

    # ✅ Completely open — no authentication, no permission check
    authentication_classes = []
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Get movie by post number. Example: ?search=postnumber1",
        manual_parameters=[
            openapi.Parameter(
                name="search",
                in_=openapi.IN_QUERY,
                description="Format: postnumber1 or postnumber42",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            200: PublicMoviePostSerializer,
            400: "Invalid format",
            404: "No movie found",
        }
    )
    def get(self, request):

        search = request.query_params.get("search", "").strip().lower()

        if not search.startswith("postnumber"):
            return Response(
                {"error": "Invalid format. Use: postnumber1 or postnumber42"},
                status=status.HTTP_400_BAD_REQUEST
            )

        number = search.replace("postnumber", "").strip()

        if not number.isdigit():
            return Response(
                {"error": "Invalid number. Use: postnumber1 or postnumber42"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            movie = MoviePost.objects.get(post_no=int(number))
        except MoviePost.DoesNotExist:
            return Response(
                {"error": f"No movie found for postnumber{number}"},
                status=status.HTTP_404_NOT_FOUND
            )

        # ✅ Track view count
        analytics, created = MovieAnalytics.objects.get_or_create(movie=movie)
        MovieAnalytics.objects.filter(id=analytics.id).update(
            view_count=F("view_count") + 1
        )

        return Response(PublicMoviePostSerializer(movie).data)


# ============================================================
# ANALYTICS
# ============================================================

class AdminAnalyticsView(APIView):

    # ✅ Admin only
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

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

        total_views = analytics.aggregate(
            total=Sum("view_count")
        )["total"] or 0

        return Response({
            "total_movies": analytics.count(),
            "total_views": total_views,
            "movies": data,
        })
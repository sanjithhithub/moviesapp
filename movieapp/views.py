from rest_framework import viewsets, status
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
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
    # Publicly accessible to create the first admin, 
    # though you might want IsAuthenticated + IsAdminUser in production
    permission_classes = [AllowAny] 

    @swagger_auto_schema(request_body=CreateAdminSerializer)
    def post(self, request):
        serializer = CreateAdminSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Account created"}, status=status.HTTP_201_CREATED)
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
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    # Critical for Image Uploads
    parser_classes = (MultiPartParser, FormParser)
    pagination_class = MoviePagination
    lookup_field = "pk"

    @swagger_auto_schema(manual_parameters=[
        openapi.Parameter('image', openapi.IN_FORM, type=openapi.TYPE_FILE, description="Movie Poster Image")
    ])
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        
        # When handling files, pass request.FILES explicitly if data is not parsing
        serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=partial
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

# ============================================================
# PUBLIC MOVIE LIST
# ============================================================

class PublicMovieList(ListAPIView):
    queryset = MoviePost.objects.all().order_by("-created_at")
    serializer_class = PublicMoviePostSerializer
    pagination_class = MoviePagination
    authentication_classes = []
    permission_classes = [AllowAny]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.query_params.get("search", "").strip()
        if search:
            queryset = queryset.filter(movie_name__icontains=search)
        return queryset

# ============================================================
# PUBLIC MOVIE DETAIL
# ============================================================

class PublicMovieDetail(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Search movie by postnumber or movie name. Partial names return suggestions.",
        manual_parameters=[
            openapi.Parameter(
                name="search",
                in_=openapi.IN_QUERY,
                description="postnumber5 or movie name (partial ok)",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
    )
    def get(self, request):
        search = request.query_params.get("search", "").strip().lower()
        if not search:
            return Response({"error": "Search parameter required"}, status=400)

        # --- postnumber exact match → single detail ---
        if search.startswith("postnumber"):
            number_str = search.replace("postnumber", "").strip()
            if not number_str.isdigit():
                return Response({"error": "Invalid number."}, status=status.HTTP_400_BAD_REQUEST)
            try:
                movie = MoviePost.objects.get(post_no=int(number_str))
            except MoviePost.DoesNotExist:
                return Response({"error": "No movie found"}, status=status.HTTP_404_NOT_FOUND)
            analytics, _ = MovieAnalytics.objects.get_or_create(movie=movie)
            MovieAnalytics.objects.filter(id=analytics.id).update(view_count=F("view_count") + 1)
            return Response(PublicMoviePostSerializer(movie, context={'request': request}).data)

        # --- if search is purely numeric, try post_no lookup ---
        if search.isdigit():
            try:
                movie = MoviePost.objects.get(post_no=int(search))
                analytics, _ = MovieAnalytics.objects.get_or_create(movie=movie)
                MovieAnalytics.objects.filter(id=analytics.id).update(view_count=F("view_count") + 1)
                return Response(PublicMoviePostSerializer(movie, context={'request': request}).data)
            except MoviePost.DoesNotExist:
                pass

        # --- movie name search ---
        movies = MoviePost.objects.filter(movie_name__icontains=search)

        if not movies.exists():
            return Response({"error": "No movie found"}, status=status.HTTP_404_NOT_FOUND)

        # Exact single match → return full detail
        exact = movies.filter(movie_name__iexact=search)
        if exact.exists():
            movie = exact.first()
            analytics, _ = MovieAnalytics.objects.get_or_create(movie=movie)
            MovieAnalytics.objects.filter(id=analytics.id).update(view_count=F("view_count") + 1)
            return Response(PublicMoviePostSerializer(movie, context={'request': request}).data)

        # Partial / multiple matches → return suggestions list (no view count increment)
        data = [
            {
                "id": movie.id,
                "movie_name": movie.movie_name,
                "post_no": movie.post_no,
                "image": movie.image.url if movie.image else None,
            }
            for movie in movies[:10]
        ]
        return Response({"suggestions": data})

# ============================================================
# ANALYTICS
# ============================================================

class AdminAnalyticsView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Optimization: select_related fetches MoviePost in the same query
        analytics_qs = MovieAnalytics.objects.select_related("movie").all()

        data = [
            {
                "post_no": item.movie.post_no,
                "movie_name": item.movie.movie_name,
                "view_count": item.view_count,
                "last_viewed": item.last_viewed,
            }
            for item in analytics_qs
        ]

        total_views = analytics_qs.aggregate(total=Sum("view_count"))["total"] or 0

        return Response({
            "total_movies": analytics_qs.count(),
            "total_views": total_views,
            "movies": data,
        })
        
        # views.py
from django.http import JsonResponse

def health_check(request):
    return JsonResponse({"status": "ok"})
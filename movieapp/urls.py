from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework import permissions
from rest_framework_simplejwt.views import TokenRefreshView
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from .views import (
    AdminMovieViewSet,
    PublicMovieList,
    PublicMovieDetail,
    AdminTokenView,
    AdminAnalyticsView,   # 👈 NEW
)

router = DefaultRouter()
router.register(
    r'admin/movies',
    AdminMovieViewSet,
    basename='admin-movies'
)

schema_view = get_schema_view(
    openapi.Info(
        title="Movie App API",
        default_version="v1",
        description="Admin & Public Movie APIs",
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [

    # 🌍 PUBLIC APIs
    path('movies/', PublicMovieList.as_view(), name='public-movie-list'),
    path('movies/<int:post_no>/', PublicMovieDetail.as_view(), name='public-movie-detail'),

    # 🔑 ADMIN AUTH
    path('admin/token/', AdminTokenView.as_view(), name='token_obtain_pair'),
    path('admin/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # 📊 ADMIN ANALYTICS (ADMIN ONLY)
    path('admin/analytics/', AdminAnalyticsView.as_view(), name='admin-analytics'),

    # 🔐 ADMIN CRUD
    path('', include(router.urls)),

    # 📘 DOCS
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='swagger'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='redoc'),
]

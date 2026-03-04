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
    MainAdminLoginView,
    SubAdminLoginView,
    AdminAnalyticsView,
    CreateAdminView,   # ✅ UPDATED
)

# ============================================================
# 🔁 ROUTER
# ============================================================

router = DefaultRouter()
router.register(
    r'admin/movies',
    AdminMovieViewSet,
    basename='admin-movies'
)

# ============================================================
# 📘 SWAGGER CONFIG
# ============================================================

schema_view = get_schema_view(
    openapi.Info(
        title="Movie App API",
        default_version="v1",
        description="Admin & Public Movie APIs",
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

# ============================================================
# 🌐 URL PATTERNS
# ============================================================

urlpatterns = [

    # ========================================================
    # 🌍 PUBLIC APIs
    # ========================================================

    path('movies/', PublicMovieList.as_view(), name='public-movie-list'),
    path('movies/<int:post_no>/', PublicMovieDetail.as_view(), name='public-movie-detail'),

    # ========================================================
    # 🔐 ACCOUNT CREATION (Role Selection)
    # ========================================================

    path('admin/create-account/', CreateAdminView.as_view(), name='create-admin'),

    # ========================================================
    # 🔑 LOGIN APIs
    # ========================================================

    path('admin/login/', MainAdminLoginView.as_view(), name='main-admin-login'),
    path('subadmin/login/', SubAdminLoginView.as_view(), name='sub-admin-login'),

    # ========================================================
    # 🔄 TOKEN REFRESH
    # ========================================================

    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),

    # ========================================================
    # 📊 ANALYTICS (Admin Only)
    # ========================================================

    path('admin/analytics/', AdminAnalyticsView.as_view(), name='admin-analytics'),

    # ========================================================
    # 🎬 ADMIN MOVIE CRUD
    # ========================================================

    path('', include(router.urls)),

    # ========================================================
    # 📘 API DOCUMENTATION
    # ========================================================

    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='swagger'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='redoc'),
]
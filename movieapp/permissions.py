# permissions.py

from rest_framework.permissions import BasePermission


class IsMainAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "mainadmin"


class IsSubAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "subadmin"
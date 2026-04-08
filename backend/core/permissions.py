# core/permissions.py
from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    """Only Store Admins can access."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'admin'


class IsCustomer(BasePermission):
    """Only Customers can access."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'customer'


class IsDeliveryMan(BasePermission):
    """Only Delivery Men can access."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'delivery'


class IsAdminOrReadOnly(BasePermission):
    """Admins can write; anyone authenticated can read."""
    def has_permission(self, request, view):
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return request.user.is_authenticated
        return request.user.is_authenticated and request.user.role == 'admin'
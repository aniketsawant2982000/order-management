# core/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Product, Order, OrderItem


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['name', 'email', 'role', 'is_active']
    list_filter = ['role']
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal', {'fields': ('name', 'role')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'name', 'password1', 'password2', 'role'),
        }),
    )
    search_fields = ['email', 'name']
    ordering = ['email']


admin.site.register(Product)
admin.site.register(Order)
admin.site.register(OrderItem)
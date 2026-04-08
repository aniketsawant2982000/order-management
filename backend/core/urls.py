# core/urls.py
from django.urls import path
from .views import (
    RegisterView, LoginView,
    ProductListCreateView,
    OrderListCreateView,
    AssignDeliveryView,
    UpdateOrderStatusView,
    DeliveryManListView,
)

urlpatterns = [
    # Auth
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),

    # Products
    path('products/', ProductListCreateView.as_view(), name='products'),

    # Orders
    path('orders/', OrderListCreateView.as_view(), name='orders'),
    path('orders/<int:pk>/assign/', AssignDeliveryView.as_view(), name='assign-delivery'),
    path('orders/<int:pk>/status/', UpdateOrderStatusView.as_view(), name='update-status'),

    # Utility
    path('delivery-men/', DeliveryManListView.as_view(), name='delivery-men'),
]
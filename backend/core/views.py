# core/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate, get_user_model
from django.core.cache import cache
from django.conf import settings
from .pagination import ProductPagination

from .models import Product, Order
from .serializers import (
    RegisterSerializer, UserSerializer, ProductSerializer,
    OrderCreateSerializer, OrderSerializer,
    AssignDeliverySerializer, UpdateStatusSerializer
)
from .permissions import IsAdmin, IsCustomer, IsDeliveryMan, IsAdminOrReadOnly
from .pagination import ProductPagination

User = get_user_model()


# ─── Helper ─────────────────────────────────────────────────
def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


# ─── POST /api/register/ ─────────────────────────────────────
class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            tokens = get_tokens_for_user(user)
            return Response({
                'user': UserSerializer(user).data,
                'tokens': tokens
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ─── POST /api/login/ ────────────────────────────────────────
class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        user = authenticate(request, email=email, password=password)
        if not user:
            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        tokens = get_tokens_for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'tokens': tokens
        })


# ─── Products ────────────────────────────────────────────────

class ProductListCreateView(APIView):
    permission_classes = [IsAdminOrReadOnly]

    def get(self, request):
        # Get current page number from URL (e.g. ?page=2)
        page = request.query_params.get('page', 1)
        page_size = request.query_params.get('page_size', 6)

        # Unique cache key per page so each page is cached separately
        cache_key = f'product_list_page_{page}_size_{page_size}'
        cached_data = cache.get(cache_key)

        if cached_data:
            print(f'✅ Cache HIT for page {page}')
            return Response(cached_data)

        print(f'❌ Cache MISS for page {page} — fetching from DB')
        products = Product.objects.all().order_by('-created_at')

        # Apply pagination
        paginator = ProductPagination()
        paginated_products = paginator.paginate_queryset(products, request)
        serializer = ProductSerializer(paginated_products, many=True)

        # Build paginated response
        response_data = paginator.get_paginated_response(serializer.data).data

        # Cache this page's result
        cache_ttl = getattr(settings, 'CACHE_TTL', 60 * 15)
        cache.set(cache_key, response_data, cache_ttl)

        return Response(response_data)

    def post(self, request):
        serializer = ProductSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(created_by=request.user)

            # Clear ALL product cache pages when new product added
            # We use cache.delete_pattern to wipe all page caches at once
            from django_redis import get_redis_connection
            redis_conn = get_redis_connection("default")
            # Delete all keys matching product_list_page_*
            keys = redis_conn.keys('*product_list_page_*')
            if keys:
                redis_conn.delete(*keys)
            print('🗑️ All product page caches cleared')

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
# ─── Orders ──────────────────────────────────────────────────
class OrderListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.role == 'admin':
            orders = Order.objects.all().order_by('-created_at')
        elif user.role == 'customer':
            orders = Order.objects.filter(customer=user).order_by('-created_at')
        elif user.role == 'delivery':
            orders = Order.objects.filter(assigned_delivery_man=user).order_by('-created_at')
        else:
            orders = Order.objects.none()

        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)

    def post(self, request):
        if request.user.role != 'customer':
            return Response(
                {'error': 'Only customers can create orders'},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer = OrderCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(customer=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ─── POST /api/orders/{id}/assign/ ───────────────────────────
class AssignDeliveryView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request, pk):
        try:
            order = Order.objects.get(pk=pk)
        except Order.DoesNotExist:
            return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = AssignDeliverySerializer(order, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(OrderSerializer(order).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ─── PATCH /api/orders/{id}/status/ ──────────────────────────
class UpdateOrderStatusView(APIView):
    permission_classes = [IsDeliveryMan]

    def patch(self, request, pk):
        try:
            order = Order.objects.get(pk=pk, assigned_delivery_man=request.user)
        except Order.DoesNotExist:
            return Response(
                {'error': 'Order not found or not assigned to you'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = UpdateStatusSerializer(order, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(OrderSerializer(order).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ─── GET /api/delivery-men/ ──────────────────────────────────
class DeliveryManListView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        delivery_men = User.objects.filter(role='delivery')
        serializer = UserSerializer(delivery_men, many=True)
        return Response(serializer.data)
    
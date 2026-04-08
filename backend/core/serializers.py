# core/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Product, Order, OrderItem

User = get_user_model()


# ─── User Serializers ────────────────────────────────────────
class RegisterSerializer(serializers.ModelSerializer):
    # write_only=True means password won't appear in API responses
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ['id', 'name', 'email', 'password', 'role']

    def create(self, validated_data):
        # Use create_user so password gets hashed properly
        return User.objects.create_user(**validated_data)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'name', 'email', 'role']


# ─── Product Serializer ──────────────────────────────────────
class ProductSerializer(serializers.ModelSerializer):
    # Show admin name in response, but don't require it in input
    created_by_name = serializers.CharField(source='created_by.name', read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'name', 'price', 'created_by', 'created_by_name', 'created_at']
        read_only_fields = ['created_by', 'created_at']


# ─── OrderItem Serializer ────────────────────────────────────
class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_price = serializers.DecimalField(
        source='product.price', max_digits=10, decimal_places=2, read_only=True
    )

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_name', 'product_price', 'quantity']


# ─── Order Serializers ───────────────────────────────────────
class OrderCreateSerializer(serializers.ModelSerializer):
    # Accept a list of items when creating an order
    items = OrderItemSerializer(many=True)

    class Meta:
        model = Order
        fields = ['id', 'items']

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        # Customer comes from the request (set in the view)
        order = Order.objects.create(**validated_data)
        for item in items_data:
            OrderItem.objects.create(order=order, **item)
        return order


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    delivery_man_name = serializers.CharField(
        source='assigned_delivery_man.name', read_only=True
    )

    class Meta:
        model = Order
        fields = [
            'id', 'customer', 'customer_name', 'status',
            'assigned_delivery_man', 'delivery_man_name',
            'items', 'created_at'
        ]
        read_only_fields = ['customer', 'created_at']


class AssignDeliverySerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['assigned_delivery_man']

    def validate_assigned_delivery_man(self, value):
        # Make sure the assigned user is actually a delivery person
        if value.role != 'delivery':
            raise serializers.ValidationError("User is not a delivery man.")
        return value

    def update(self, instance, validated_data):
        instance.assigned_delivery_man = validated_data['assigned_delivery_man']
        instance.status = 'assigned'
        instance.save()
        return instance


class UpdateStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['status']

    def validate_status(self, value):
        if value != 'delivered':
            raise serializers.ValidationError("Delivery man can only set status to 'delivered'.")
        return value
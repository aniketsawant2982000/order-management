# core/models.py
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


# ─── Custom User Manager ────────────────────────────────────
# Django needs this to know how to create users via CLI (createsuperuser)
class UserManager(BaseUserManager):
    def create_user(self, email, name, password=None, role='customer'):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, name=name, role=role)
        user.set_password(password)   # hashes the password
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, password=None):
        user = self.create_user(email, name, password, role='admin')
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


# ─── Custom User Model ──────────────────────────────────────
class User(AbstractBaseUser, PermissionsMixin):
    # Why custom user model?
    # Django's default uses 'username' — we want to login with email + support roles

    ROLE_CHOICES = [
        ('admin', 'Store Admin'),
        ('delivery', 'Delivery Man'),
        ('customer', 'Customer'),
    ]

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)   # needed for Django admin

    objects = UserManager()

    USERNAME_FIELD = 'email'        # login with email
    REQUIRED_FIELDS = ['name']      # required when using createsuperuser

    def __str__(self):
        return f"{self.name} ({self.role})"


# ─── Product ────────────────────────────────────────────────
class Product(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    # created_by links to the admin who added this product
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,   # if admin deleted, keep product
        null=True,
        related_name='products'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


# ─── Order ──────────────────────────────────────────────────
class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('assigned', 'Assigned'),
        ('delivered', 'Delivered'),
    ]

    id = models.AutoField(primary_key=True)
    customer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='orders'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    assigned_delivery_man = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='deliveries'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id} by {self.customer.name}"


# ─── OrderItem ──────────────────────────────────────────────
# Each Order can have multiple products — this is a "junction" table
class OrderItem(models.Model):
    id = models.AutoField(primary_key=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity}x {self.product.name}"
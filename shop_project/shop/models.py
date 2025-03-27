from django.db import models
from django.utils import timezone

# Create your models here.

class ProductManager(models.Manager):
    def in_stock(self):
        return self.filter(stock__gt=0)
    
    def by_category(self, category_name):
        return self.filter(category__name=category_name)
    
    def price_range(self, min_price, max_price):
        return self.filter(price__gte=min_price, price__lte=max_price)
    
    def search(self, query):
        return self.filter(
            models.Q(title__icontains=query) |
            models.Q(description__icontains=query)
        )

class OrderManager(models.Manager):
    def get_pending_order(self):
        return self.filter(status='pending').first()
    
    def get_customer_orders(self, customer_email):
        return self.filter(customer_email=customer_email)
    
    def get_orders_by_status(self, status):
        return self.filter(status=status)
    
    def get_orders_by_date_range(self, start_date, end_date):
        return self.filter(created_at__range=(start_date, end_date))

class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Categories"

class Product(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=6, decimal_places=2)
    image = models.ImageField(upload_to='products/', null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    stock = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ProductManager()

    def __str__(self):
        return self.title

    def is_in_stock(self):
        return self.stock > 0

    def reduce_stock(self, quantity=1):
        if self.stock >= quantity:
            self.stock -= quantity
            self.save()
            return True
        return False

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
    ]

    customer_name = models.CharField(max_length=200)
    customer_email = models.EmailField()
    products = models.ManyToManyField(Product, through='OrderItem')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = OrderManager()

    def __str__(self):
        return f"Order {self.id} - {self.customer_name}"

    def update_total(self):
        self.total_amount = sum(item.price * item.quantity for item in self.orderitem_set.all())
        self.save()

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def total(self):
        return self.price * self.quantity

    def __str__(self):
        return f"{self.quantity}x {self.product.title} in Order #{self.order.id}"

    def save(self, *args, **kwargs):
        # Update the order's total amount when an item is saved
        super().save(*args, **kwargs)
        self.order.update_total()



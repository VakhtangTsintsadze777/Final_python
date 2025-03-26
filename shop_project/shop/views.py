from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from shop.models import Product, Order, OrderItem
from django.contrib import messages
from decimal import Decimal
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.core.paginator import Paginator
from django.db.models import Q

# Create your views here.

# Class-based views
class ProductListView(ListView):
    model = Product
    template_name = 'home.html'
    context_object_name = 'products'
    paginate_by = 3  # Changed from 8 to 3 products per page

    def get_queryset(self):
        queryset = Product.objects.all()
        search_query = self.request.GET.get('search')
        category = self.request.GET.get('category')
        min_price = self.request.GET.get('min_price')
        max_price = self.request.GET.get('max_price')

        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query)
            )
        if category:
            queryset = queryset.filter(category__name=category)
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)

        return queryset

class ProductDetailView(DetailView):
    model = Product
    template_name = 'product_detail.html'
    context_object_name = 'product'

class ProductCreateView(LoginRequiredMixin, CreateView):
    model = Product
    template_name = 'product_form.html'
    fields = ['title', 'description', 'price', 'category', 'stock', 'is_active']
    success_url = reverse_lazy('home')

class ProductUpdateView(LoginRequiredMixin, UpdateView):
    model = Product
    template_name = 'product_form.html'
    fields = ['title', 'description', 'price', 'category', 'stock', 'is_active']
    success_url = reverse_lazy('home')

class ProductDeleteView(LoginRequiredMixin, DeleteView):
    model = Product
    template_name = 'product_confirm_delete.html'
    success_url = reverse_lazy('home')

# Function-based views
def about_view(request):
    return render(request, "about.html")

def add_to_cart(request, product_id):
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id)
        
        if not product.is_in_stock():
            messages.error(request, f'Sorry, {product.title} is out of stock!')
            return redirect('home')
        
        # Get or create the order
        order, created = Order.objects.get_or_create(
            customer_name=request.POST.get('customer_name', 'Guest'),
            customer_email=request.POST.get('customer_email', 'guest@example.com'),
            status='pending',
            defaults={'total_amount': Decimal('0.00')}
        )
        
        # Create order item
        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=1,
            price=product.price
        )
        
        messages.success(request, f'{product.title} added to cart!')
        return redirect('home')
    
    return redirect('home')

def view_cart(request):
    # Get the current pending order for the user
    order = Order.objects.filter(status='pending').first()
    
    if order:
        # Get all items in the cart
        items = OrderItem.objects.filter(order=order)
        
        # Calculate totals
        subtotal = sum(item.total for item in items)
        shipping_cost = len(items)  # $1 per item
        total = subtotal + shipping_cost
        
        return render(request, 'cart.html', {
            'items': items,
            'subtotal': subtotal,
            'shipping_cost': shipping_cost,
            'total': total,
        })
    else:
        return render(request, 'cart.html', {
            'items': None,
            'subtotal': 0,
            'shipping_cost': 0,
            'total': 0,
        })

def remove_from_cart(request, item_id):
    if request.method == 'POST':
        item = get_object_or_404(OrderItem, id=item_id)
        order = item.order
        product = item.product
        product_title = product.title
        
        # Delete the item
        item.delete()
        
        # Update order total
        if order.orderitem_set.exists():
            order.update_total()
        else:
            # If no items left, delete the order
            order.delete()
        
        messages.success(request, f'{product_title} removed from cart!')
        return redirect('view_cart')
    
    return redirect('view_cart')

def checkout(request):
    if request.method == 'POST':
        order = Order.objects.filter(status='pending').first()
        
        if not order:
            messages.error(request, 'No items in cart')
            return redirect('view_cart')
            
        items = OrderItem.objects.filter(order=order)
        
        # Check stock availability
        for item in items:
            if item.quantity > item.product.stock:
                messages.error(request, f'Not enough stock for {item.product.title}')
                return redirect('view_cart')
        
        # Calculate totals
        subtotal = sum(item.total for item in items)
        shipping_cost = len(items)  # $1 per item
        total = subtotal + shipping_cost
        
        # Update stock and order
        try:
            for item in items:
                item.product.stock -= item.quantity
                item.product.save()
            
            order.total_amount = total
            order.status = 'processing'
            order.save()
            
            messages.success(request, 'Order placed successfully!')
            return redirect('home')
            
        except Exception as e:
            messages.error(request, 'Error processing order')
            return redirect('view_cart')
    
    return redirect('view_cart')

def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        
        # Basic validation
        if password1 != password2:
            messages.error(request, 'Passwords do not match!')
            return redirect('register')
            
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists!')
            return redirect('register')
            
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered!')
            return redirect('register')
        
        # Create user
        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password1
            )
            messages.success(request, 'Account created successfully! Please log in.')
            return redirect('login')
        except Exception as e:
            messages.error(request, 'Error creating account. Please try again.')
            return redirect('register')
    
    return render(request, 'register.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, 'Welcome back!')
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')
 

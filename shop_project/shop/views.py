from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, Http404
from shop.models import Product, Order, OrderItem, Category
from django.contrib import messages
from decimal import Decimal
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.core.exceptions import ValidationError
from django.http import JsonResponse
import logging
from django.views.decorators.http import require_POST
import json

from .forms import ProductForm, OrderForm, OrderItemForm, ProductSearchForm

logger = logging.getLogger(__name__)

# Create your views here.

# Class-based views
class ProductListView(ListView):
    model = Product
    template_name = 'home.html'
    context_object_name = 'products'
    paginate_by = 3

    def get_queryset(self):
        try:
            queryset = Product.objects.active()
            form = ProductSearchForm(self.request.GET)
            
            if form.is_valid():
                search_query = form.cleaned_data.get('search')
                category = form.cleaned_data.get('category')
                min_price = form.cleaned_data.get('min_price')
                max_price = form.cleaned_data.get('max_price')
                sort = form.cleaned_data.get('sort', '')

                if search_query:
                    queryset = queryset.search(search_query)
                if category:
                    queryset = queryset.filter(category=category)
                if min_price is not None:
                    queryset = queryset.filter(price__gte=min_price)
                if max_price is not None:
                    queryset = queryset.filter(price__lte=max_price)

                # Handle sorting
                if sort:
                    if sort == 'price_asc':
                        queryset = queryset.order_by('price')
                    elif sort == 'price_desc':
                        queryset = queryset.order_by('-price')
                    elif sort == 'name_asc':
                        queryset = queryset.order_by('title')
                    elif sort == 'name_desc':
                        queryset = queryset.order_by('-title')
                    elif sort == 'category_asc':
                        queryset = queryset.order_by('category__name')
                    elif sort == 'category_desc':
                        queryset = queryset.order_by('-category__name')
                    elif sort == 'newest':
                        queryset = queryset.order_by('-created_at')
                    elif sort == 'oldest':
                        queryset = queryset.order_by('created_at')
                else:
                    # Default sorting by oldest first
                    queryset = queryset.order_by('created_at')

            return queryset
        except Exception as e:
            logger.error(f"Error in ProductListView.get_queryset: {str(e)}")
            messages.error(self.request, "An error occurred while loading products.")
            return Product.objects.none()

    def get_context_data(self, **kwargs):
        try:
            context = super().get_context_data(**kwargs)
            context['form'] = ProductSearchForm(self.request.GET)
            context['sort'] = self.request.GET.get('sort', '')
            context['categories'] = Category.objects.filter(is_active=True)
            return context
        except Exception as e:
            logger.error(f"Error in ProductListView.get_context_data: {str(e)}")
            messages.error(self.request, "An error occurred while loading the page.")
            return {}

class ProductDetailView(DetailView):
    model = Product
    template_name = 'product_detail.html'
    context_object_name = 'product'

    def get_context_data(self, **kwargs):
        try:
            context = super().get_context_data(**kwargs)
            if self.request.user.is_authenticated:
                context['customer_name'] = self.request.user.username
                context['customer_email'] = self.request.user.email
            else:
                context['customer_name'] = 'Guest'
                context['customer_email'] = 'guest@example.com'
            return context
        except Exception as e:
            logger.error(f"Error in ProductDetailView.get_context_data: {str(e)}")
            messages.error(self.request, "An error occurred while loading the product details.")
            return {}

class ProductCreateView(LoginRequiredMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'product_form.html'
    success_url = reverse_lazy('home')

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            messages.success(self.request, 'Product created successfully!')
            return response
        except Exception as e:
            logger.error(f"Error in ProductCreateView.form_valid: {str(e)}")
            messages.error(self.request, 'An error occurred while creating the product.')
            return self.form_invalid(form)

class ProductUpdateView(LoginRequiredMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'product_form.html'
    success_url = reverse_lazy('home')

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            messages.success(self.request, 'Product updated successfully!')
            return response
        except Exception as e:
            logger.error(f"Error in ProductUpdateView.form_valid: {str(e)}")
            messages.error(self.request, 'An error occurred while updating the product.')
            return self.form_invalid(form)

class ProductDeleteView(LoginRequiredMixin, DeleteView):
    model = Product
    template_name = 'product_confirm_delete.html'
    success_url = reverse_lazy('home')

    def delete(self, request, *args, **kwargs):
        try:
            response = super().delete(request, *args, **kwargs)
            messages.success(self.request, 'Product deleted successfully!')
            return response
        except Exception as e:
            logger.error(f"Error in ProductDeleteView.delete: {str(e)}")
            messages.error(self.request, 'An error occurred while deleting the product.')
            return redirect(self.success_url)

class OrderListView(LoginRequiredMixin, ListView):
    model = Order
    template_name = 'orders.html'
    context_object_name = 'orders'
    ordering = ['-created_at']

    def get_queryset(self):
        try:
            return Order.objects.get_customer_orders(self.request.user.email)
        except Exception as e:
            logger.error(f"Error in OrderListView.get_queryset: {str(e)}")
            messages.error(self.request, "An error occurred while loading your orders.")
            return Order.objects.none()

# Function-based views
def about_view(request):
    return render(request, "about.html")

def add_to_cart(request, product_id):
    if request.method == 'POST':
        try:
            product = get_object_or_404(Product, id=product_id)
            
            if not product.is_in_stock():
                messages.error(request, f'Sorry, {product.title} is out of stock!')
                return redirect('home')
            
            if request.user.is_authenticated:
                customer_email = request.user.email
                customer_name = request.user.username
            else:
                customer_email = 'guest@example.com'
                customer_name = 'Guest'
            
            order, created = Order.objects.get_or_create(
                customer_name=customer_name,
                customer_email=customer_email,
                status='pending',
                defaults={'total_amount': Decimal('0.00')}
            )
            
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=1,
                price=product.price
            )
            
            messages.success(request, f'{product.title} added to cart!')
            return redirect('home')
        except Exception as e:
            logger.error(f"Error in add_to_cart: {str(e)}")
            messages.error(request, "An error occurred while adding the item to cart.")
            return redirect('home')
    
    return redirect('home')

def view_cart(request):
    try:
        order = Order.objects.get_pending_order()
        
        if order:
            items = OrderItem.objects.filter(order=order)
            subtotal = sum(item.total for item in items)
            shipping_cost = len(items)
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
    except Exception as e:
        logger.error(f"Error in view_cart: {str(e)}")
        messages.error(request, "An error occurred while loading your cart.")
        return render(request, 'cart.html', {
            'items': None,
            'subtotal': 0,
            'shipping_cost': 0,
            'total': 0,
        })

def remove_from_cart(request, item_id):
    if request.method == 'POST':
        try:
            item = get_object_or_404(OrderItem, id=item_id)
            order = item.order
            product = item.product
            product_title = product.title
            
            item.delete()
            
            if order.orderitem_set.exists():
                order.update_total()
            else:
                order.delete()
            
            messages.success(request, f'{product_title} removed from cart!')
            return redirect('view_cart')
        except Exception as e:
            logger.error(f"Error in remove_from_cart: {str(e)}")
            messages.error(request, "An error occurred while removing the item from cart.")
            return redirect('view_cart')
    
    return redirect('view_cart')

def checkout(request):
    if request.method == 'POST':
        try:
            order = Order.objects.get_pending_order()
            
            if not order:
                messages.error(request, 'No items in cart')
                return redirect('view_cart')
            
            # Check if all items are in stock before proceeding
            for item in order.orderitem_set.all():
                if item.product.stock < item.quantity:
                    messages.error(request, f'Sorry, {item.product.title} is out of stock!')
                    return redirect('view_cart')
            
            # Reduce stock for each item
            for item in order.orderitem_set.all():
                item.product.reduce_stock(item.quantity)
                
            order.status = 'processing'
            order.save()
            
            messages.success(request, 'Order placed successfully!')
            return redirect('home')
        except Exception as e:
            logger.error(f"Error in checkout: {str(e)}")
            messages.error(request, "An error occurred while processing your order.")
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

def orders_view(request):
    if request.user.is_authenticated:
        orders = Order.objects.filter(customer_email=request.user.email)
    else:
        orders = Order.objects.filter(customer_email='guest@example.com')
    
    orders = orders.order_by('-created_at')
    return render(request, 'orders.html', {'orders': orders})

@require_POST
def update_theme(request):
    try:
        data = json.loads(request.body)
        theme = data.get('theme')
        if theme in ['light', 'dark']:
            request.session['theme'] = theme
            return JsonResponse({'status': 'success'})
        return JsonResponse({'status': 'error', 'message': 'Invalid theme'}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
 

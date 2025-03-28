from .models import Order, OrderItem

def cart_count(request):
    if request.user.is_authenticated:
        # For authenticated users, get their pending order
        order = Order.objects.filter(
            customer_email=request.user.email,
            status='pending'
        ).first()
    else:
        # For guest users, get the first pending order
        order = Order.objects.filter(
            customer_email='guest@example.com',
            status='pending'
        ).first()
    
    if order:
        return {'cart_count': OrderItem.objects.filter(order=order).count()}
    return {'cart_count': 0} 
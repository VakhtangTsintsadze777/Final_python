from .models import Order, OrderItem

def cart_count(request):
    try:
        order = Order.objects.filter(status='pending').first()
        if order:
            count = OrderItem.objects.filter(order=order).count()
        else:
            count = 0
    except:
        count = 0
    return {'cart_count': count} 
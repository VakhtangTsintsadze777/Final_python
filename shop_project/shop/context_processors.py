from .models import Order, OrderItem

def cart_count(request):
    order = Order.objects.get_pending_order()
    if order:
        count = order.orderitem_set.count()
    else:
        count = 0
    return {'cart_count': count} 
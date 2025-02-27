from django.shortcuts import render, redirect
from django.core.cache import cache
import shopify
from shopify_app.decorators import shop_login_required

@shop_login_required
def index(request):
    products = shopify.Product.find(limit=3)
    orders = shopify.Order.find(order="created_at DESC")
    days = cache.get('days', '')
    time = cache.get('time', '')
    print(days,time)
    return render(request, 'home/index.html', {'products': products, 'orders': orders,'days': days, 'time': time})

def clear_session(request):
    request.session.flush()
    return redirect('root_path')  # Redirect to the index view or any other view


def store_days_time(request):
    if request.method == 'POST':
        days = request.POST.get('days')
        time = request.POST.get('time')
        cache.set('days', days)
        cache.set('time', time)
        return redirect('root_path')
    
    # Retrieve data from cache
    days = cache.get('days', '')
    time = cache.get('time', '')
    return render(request, 'home/index.html', {'days': days, 'time': time})
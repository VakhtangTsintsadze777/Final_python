from django.urls import path
from . import views

urlpatterns = [
    path("", views.ProductListView.as_view(), name="home"),
    path("about/", views.about_view, name="about"),
    path("product/<int:pk>/", views.ProductDetailView.as_view(), name="product-detail"),
    path("product/new/", views.ProductCreateView.as_view(), name="product-create"),
    path("product/<int:pk>/edit/", views.ProductUpdateView.as_view(), name="product-update"),
    path("product/<int:pk>/delete/", views.ProductDeleteView.as_view(), name="product-delete"),
    path("add-to-cart/<int:product_id>/", views.add_to_cart, name="add-to-cart"),
    path("cart/", views.view_cart, name="view_cart"),
    path("remove-from-cart/<int:item_id>/", views.remove_from_cart, name="remove-from-cart"),
    path("checkout/", views.checkout, name="checkout"),
    path("register/", views.register, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
] 
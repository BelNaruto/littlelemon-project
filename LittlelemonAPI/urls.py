from django.urls import path
from . import views

urlpatterns = [
    path('menu-items/', views.menu_items),
    path('menu-items/<int:menuItem_id>', views.single_item),
    path('groups/manager/users', views.managers),
    path('groups/manager/users/<int:id>', views.managers_delete),
    path('groups/delivery-crew/users', views.delivery_crew),
    path('groups/delivery-crew/users/<int:userId>', views.remove_delivery_crew),
    # Cart management endpoints 
    path('groups/cart/menu-items', views.cart_menu),
    # Order management endpoints
    path('orders', views.orders),
    path('orders/<int:orderId>', views.orders_transit),
     
]

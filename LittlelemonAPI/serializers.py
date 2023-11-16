from rest_framework import serializers
from .models import Category, MenuItem, Cart, Order, OrderItem
from django.contrib.auth.models import User


class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']  
    
    def to_representation(self, instance):
        data=super().to_representation(instance)
        data.pop('password', None)
        return data
        # Exclude 'password'

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'slug', 'title']

class MenuItemSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    class Meta:
        model = MenuItem
        fields = ['id', 'title','price','featured', 'category',]

class CartSerializer(serializers.ModelSerializer):
    
    user = CustomUserSerializer()  # User serializer
    class Meta:
        model = Cart
        fields = ['id', 'quantity', 'unit_price', 'price', 'user', 'menuitem']
        depth=1
class OrderSerializer(serializers.ModelSerializer):
   # order_items = OrderItemSerializer(many=True, read_only=True)
    user = CustomUserSerializer()  # User serializer
    class Meta:
        model = Order
        fields = ['id', 'status', 'total', 'date', 'user', 'delivery_crew']
class OrderItemSerializer(serializers.ModelSerializer):
    menuitem = MenuItemSerializer(read_only=True)
    order = OrderSerializer(read_only=True)
    class Meta:
        model = OrderItem
        fields = ['id', 'quantity', 'unit_price', 'price', 'order', 'menuitem']
        




from django.shortcuts import render
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from .models import MenuItem, Category, Cart, Order, OrderItem
from .serializers import MenuItemSerializer, OrderSerializer, CartSerializer, OrderItemSerializer
from rest_framework import status
from django.core.paginator import Paginator, EmptyPage
from rest_framework.permissions import IsAuthenticated, IsAdminUser, BasePermission
from django.contrib.auth.models import User, Group
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage
from rest_framework.throttling import UserRateThrottle
from .throttles import TenCallsPerMinute
# To check users
from .permissions import IsReadOnlyForCertainGroups



            
class IsManagerPermission(BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(name="Manager").exists()

class IsCustomerOrDeliveryCrewPermission(BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(name__in=["Customer", "delivery crew"]).exists()

# Check if his a delivery Person
class IsDeliveryPermission(BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(name="delivery crew").exists()

# Class for Customers
class NoGroupPermission(BasePermission):
    def has_permission(self, request, view):
        return not request.user.groups.exists()

# Views

@api_view(['GET', 'POST', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsCustomerOrDeliveryCrewPermission | IsManagerPermission | IsAdminUser])
@throttle_classes([TenCallsPerMinute])
def menu_items(request):
    if request.method == 'GET':
        # List all menu items
        items = MenuItem.objects.select_related('category').all()
        category_name=request.query_params.get('category')
        to_price=request.query_params.get('to_price')
        search=request.query_params.get('search')
        # pagination
        perpage=request.query_params.get('perpage', default=2)
        page=request.query_params.get('page', default=1)   
        # Ordering
        ordering=request.query_params.get('ordering')
        # Filter for category & price & search
        if category_name:
            
            items= items.filter(category__title= category_name)
            if to_price:
                
                #price__lte price less than or equal to
                items=items.filter(price__lte=to_price)
        if search:
            
            #title__startswith
            #title__contains - search for the text anywhere in the title
            #title__icontains - case insensitive
            items=items.filter(title__istartswith=search) 
        
        # Ordering
        if ordering:
            
        #    items=items.order_by(ordering) 
           # to get more than one value
            ordering_fields=ordering.split(",")
            items=items.order_by(*ordering_fields)  
        # initialize the paginator object
        paginator=Paginator(items, per_page=perpage)
        try:
            items=paginator.page(number=page)
        except EmptyPage:
           items=[]     
             
        serialized_items = MenuItemSerializer(items, many=True)
        return Response(serialized_items.data, status=status.HTTP_200_OK)
    elif request.method == 'POST':
        # Created a new menu item (only allowed for Managers)
        if IsManagerPermission().has_permission(request, None):
            serialized_item = MenuItemSerializer(data=request.data)
            if serialized_item.is_valid():
                serialized_item.save()
                return Response(serialized_item.data, status=status.HTTP_201_CREATED)
            else:
                return Response(serialized_item.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"message": "You are not authorized to create menu items"}, status=status.HTTP_403_FORBIDDEN)
    elif request.method == 'PUT' or request.method == 'PATCH':
        # Updated menu items (only allowed for Managers)
        if IsManagerPermission().has_permission(request, None):
            # Implement the logic to update menu items
            pass
            return Response({"message": "Menu item updated successfully"}, status=status.HTTP_200_OK)
        else:
            return Response({"message": "You are not authorized to update menu items"}, status=status.HTTP_403_FORBIDDEN)
    elif request.method == 'DELETE':
        # Deleted menu items (only allowed for Managers)
        if IsManagerPermission().has_permission(request, None):
            
            pass
            return Response({"message": "Menu items deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
        else:
            return Response({"message": "You are not authorized to delete menu items"}, status=status.HTTP_403_FORBIDDEN)

@api_view(['GET', 'POST', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsCustomerOrDeliveryCrewPermission | IsManagerPermission])
def single_item(request, menuItem_id):
    if request.method == 'GET':
        # List a single menu item
        item = get_object_or_404(MenuItem, pk=menuItem_id)
        serialized_item = MenuItemSerializer(item)
        return Response(serialized_item.data, status=status.HTTP_200_OK)
    elif request.method == 'POST':
        # Deny access to create menu items
        return Response({"message": "You are not authorized to create menu items"}, status=status.HTTP_403_FORBIDDEN)
    elif request.method in ['PUT', 'PATCH']:
        # Update menu items (only allowed for Managers)
        if IsManagerPermission().has_permission(request, None):
            # Implement the logic to update a single menu item
            pass
            return Response({"message": "Menu item updated successfully"}, status=status.HTTP_200_OK)
        else:
            return Response({"message": "You are not authorized to update a single menu item"}, status=status.HTTP_403_FORBIDDEN)
    elif request.method == 'DELETE':
        # Deny access to delete menu items
        return Response({"message": "You are not authorized to delete menu items"}, status=status.HTTP_403_FORBIDDEN)       
        
        


# For Managers
@api_view(['GET','POST'])
@permission_classes([IsAuthenticated, IsManagerPermission])
def managers(request):
    if request.method == 'GET':
        # Retrieve a list of managers
        managers = User.objects.filter(groups__name="Manager")
        manager_data = [{'id': manager.id, 'username': manager.username} for manager in managers]
        return Response(manager_data, status=status.HTTP_200_OK)
    
    elif request.method == 'POST':
        # Assign the user in the payload to the "Manager" group
        username = request.data.get('username', None)
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({"message": f"User with username '{username}' does not exist."}, status=status.HTTP_404_NOT_FOUND)

        manager_group, created = Group.objects.get_or_create(name="Manager")
        user.groups.add(manager_group)
        return Response({"message": f"User '{username}' assigned to the 'Manager' group."}, status=status.HTTP_201_CREATED)
    
# REMOVING users from managers
# For Managers
@api_view(['DELETE'])
@throttle_classes([TenCallsPerMinute])
@permission_classes([IsAuthenticated, IsManagerPermission])
def managers_delete(request, id):
    try:
        user = User.objects.get(id=id)
    except User.DoesNotExist:
        return Response({"message": "User not found."}, status=status.HTTP_404_NOT_FOUND)

    manager_group, _ = Group.objects.get_or_create(name="Manager")
    
    if manager_group in user.groups.all():
        user.groups.remove(manager_group)
        return Response({"message": f"User {user.username} removed from the 'Manager' group."}, status=status.HTTP_200_OK)
    else:
        return Response({"message": "User is not a member of the 'Manager' group."}, status=status.HTTP_200_OK)
    
    
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated, IsManagerPermission])
def delivery_crew(request):
    if request.method == 'GET':
        # Retrieve a list of all the delivery_crew
        delivery_crew = User.objects.filter(groups__name="delivery crew")
        delivery_data = [{'id': delivery.id, 'username': delivery.username} for delivery in delivery_crew]
        return Response(delivery_data, status=status.HTTP_200_OK)
    elif request.method == 'POST':
        # user in the payload to the "delivery crew" group
        username = request.data.get('username', None)
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({"message": f"User with username '{username}' does not exist."}, status=status.HTTP_404_NOT_FOUND)

        delivery_crew_group, _ = Group.objects.get_or_create(name="delivery crew")
        user.groups.add(delivery_crew_group)
        return Response({"message": f"User '{username}' assigned to the 'delivery crew' group."}, status=status.HTTP_201_CREATED)
    


@api_view(['DELETE'])
@permission_classes([IsAuthenticated, IsManagerPermission])
def remove_delivery_crew(request,userId):
    
    try:
        user = User.objects.get(id=userId)
    except User.DoesNotExist:
        return Response({"message": "User not found."}, status=status.HTTP_404_NOT_FOUND)

    manager_group, _ = Group.objects.get_or_create(name="delivery crew")
    
    if manager_group in user.groups.all():
        user.groups.remove(manager_group)
        return Response({"message": f"User {user.username} removed from the 'delivery crew' group."}, status=status.HTTP_200_OK)
    else:
        return Response({"message": "User is not a member of the 'delivery crew' group."}, status=status.HTTP_200_OK)
    

# Cart 
@api_view(['GET', 'POST', 'DELETE'])
@permission_classes([IsAuthenticated, NoGroupPermission])       
def cart_menu(request):
    user= request.user
    if request.method == 'GET':
        
        cart_items = Cart.objects.filter(user=user)
        cart_data=CartSerializer(cart_items, many=True)
        return Response(cart_data.data, status=status.HTTP_200_OK)
    elif request.method == 'POST':
                # Get the menu item ID from the request data
        menu_item_id = request.data.get('menuitem')
        quantity = request.data.get('quantity')
        unit_price = request.data.get('unit_price')
        price = request.data.get('price')
        
        try:
            menu_item = MenuItem.objects.get(id=menu_item_id)
        except MenuItem.DoesNotExist:
            return Response({"message": "Menu item not found."}, status=status.HTTP_404_NOT_FOUND)
        # Create a new cart item for the user
        cart_item = Cart(user=request.user, menuitem=menu_item,quantity=quantity, unit_price=unit_price, price=(price))
        cart_item.save()
        
        cart_data = CartSerializer(cart_item)
        return Response(cart_data.data, status=status.HTTP_201_CREATED)
    elif request.method == 'DELETE':
        cart_item_delete = Cart.objects.filter(user=request.user)
        if cart_item_delete.exists():
            cart_item_delete.delete()
            return Response({"message": "The cart was emptied."}, status=status.HTTP_200_OK)
        else:
            return Response({"message": "Menu item not found."}, status=status.HTTP_404_NOT_FOUND)
            


@api_view(['GET', 'POST'])
@throttle_classes([UserRateThrottle])
@permission_classes([IsAuthenticated, NoGroupPermission | IsManagerPermission | IsDeliveryPermission])  
def orders(request):
    if request.method == 'GET':
        if NoGroupPermission().has_permission(request, None):
            orders= Order.objects.filter(user=request.user)
            order_item=OrderSerializer(orders, many=True)
            return Response(order_item.data, status=status.HTTP_200_OK)
        #Checking if he/she is a manager
        elif IsManagerPermission().has_permission(request, None):
            # Filtering, ordering and pagination
            search=request.query_params.get('search')
            ordering=request.query_params.get('ordering')
            perpage=request.query_params.get('perpage', default=2)
            page=request.query_params.get('page', default=1)           
            
            
            orders=Order.objects.all()
            if search:
                orders=orders.filter(user=search)
            if ordering:
                orders=orders.order_by(ordering)
            
            paginator=Paginator(orders, per_page=perpage)
            try:
                orders=paginator.page(number=page)
            except EmptyPage:
                orders = []
                
                
            order_item=OrderSerializer(orders, many=True)
            return Response(order_item.data, status=status.HTTP_200_OK)
        #Check if is a delivery Person
        if IsDeliveryPermission().has_permission(request, None):
            orders=OrderItem.objects.filter(order__delivery_crew=request.user)
            order_item=OrderItemSerializer(orders, many=True)
            return Response(order_item.data, status=status.HTTP_200_OK)
            
            
        
    elif request.method== 'POST':
        if NoGroupPermission().has_permission(request, None):
            # Get current cart items for the user
            cart_items = Cart.objects.filter(user=request.user)
            if cart_items.exists():
                #Create a new order for the user
                order=Order.objects.create(user=request.user, total=0, date=timezone.now(), status=False)
                
                # Create order items from cart items
                for cart_item in cart_items:
                    order_item_data={
                        'order':order.id,
                        'menuitem':cart_item.menuitem.id,
                        'quantity':cart_item.quantity,
                        'unit_price':cart_item.unit_price,
                        'price':cart_item.price,
                    }
                    order_item_serializer=OrderItemSerializer(data=order_item_data)
                    order_item_serializer.is_valid(raise_exception=True)
                    order_item_serializer.save()
                
                # Calculate the total for the order
                order.total= sum([item.price for item in order.orderitem_set.all()])
                order.save()
            
                
                
                # Delete all items from the cart for this user
                cart_item.delete()
                cart_items.delete()
                Cart.objects.filter(user=request.user).delete()
                
                
                
                return Response({"message": "Order item created and cart emptied successfully."}, status=status.HTTP_201_CREATED)
            else:
                return Response({"message": "No cart items found for the user."}, status=status.HTTP_404_NOT_FOUND)




@api_view(['GET', 'POST', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated, NoGroupPermission | IsManagerPermission | IsDeliveryPermission])
def orders_transit(request, orderId):
    # Check if this order exists
    try:
        order=Order.objects.get(id=orderId)
    except Order.DoesNotExist:
        return Response({"message": "Order not found."}, status=status.HTTP_404_NOT_FOUND)
        
        
    if request.method == 'GET':
        
        #Check for Customer
        if NoGroupPermission().has_permission(request, None):
            try:
               # orders=Order.objects.get(id=orderId)
                if order.user_id == request.user.id:
                    order_item=OrderSerializer(order)
                    return Response(order_item.data, status=status.HTTP_200_OK)
                else:
                    return Response({"message":"This order doesn't belong to you"}, status=status.HTTP_401_UNAUTHORIZED)
            except Order.DoesNotExist:  
                return Response({"message": "Something went wrong."}, status=status.HTTP_404_NOT_FOUND)
    
    elif request.method in ['PUT', 'PATCH']:
        ##Check for Manager
        if IsManagerPermission().has_permission(request, None):
            delivery_crew_id=request.data.get('delivery_crew')
            status_value=request.data.get('status')
            
            # Validate delivery_crew_id and status
            if delivery_crew_id is not None:
                try:
                    delivery_crew=User.objects.get(id=delivery_crew_id, groups__name="delivery crew")
                    order.delivery_crew=delivery_crew
                except User.DoesNotExist:
                    return Response({"message": "Delivery crew not found."}, status=status.HTTP_404_NOT_FOUND)
                
                if status_value is not None:
                    order.status=status_value
                    
                
                order.save()
                
                order_serializer=OrderSerializer(order)
                return Response(order_serializer.data, status=status.HTTP_200_OK)
            # Only for delivery Crew
        elif IsDeliveryPermission().has_permission(request, None) and request.method == 'PATCH':
            status_value=request.data.get('status')
            if status_value is not None:
                try:
                    order=Order.objects.get(id=orderId, delivery_crew=request.user)
                except Order.DoesNotExist:
                    return Response({"message": "Order not found or not assigned to the delivery crew."}, status=status.HTTP_404_NOT_FOUND)
                #Update only the status for the order
                order.status=status_value
                order.save()
                
                order_serializer=OrderSerializer(order)
                return Response(order_serializer.data, status=status.HTTP_200_OK)
        else:
            
            Response({"message": "Invalid data provided for updating the order."}, status=status.HTTP_400_BAD_REQUEST)
                    
            
            
    elif request.method == 'DELETE':
        if IsManagerPermission().has_permission(request, None):
            try:
                order.delete()
                return Response({"message": "Order deleted successfully"}, status=status.HTTP_200_OK)
            except Order.DoesNotExist:
                return Response({"message": "Order not found."}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({"message": "You are not authorized to delete this order"}, status=status.HTTP_403_FORBIDDEN)
                
                
            
            
            
            
    
    # Return a default response for unsupported methods
    return Response({"message": "Something went wrong please check your credentials."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
            
                    
                    
        
        
                    

            
            
            
            
            
            
            
            
            
        
        
        
        
        
    
    


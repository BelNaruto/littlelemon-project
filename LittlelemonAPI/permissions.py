from rest_framework import permissions

class IsReadOnlyForCertainGroups(permissions.BasePermission):
    def has_permission(self, request, view):
        # Check if the user is in the 'Customer' or 'delivery crew' groups
        user = request.user
        if user.groups.filter(name__in=['Customer', 'delivery crew']).exists():
            # Deny access to POST, PUT, PATCH, and DELETE methods
            return request.method == 'GET'
        # Allow other users to access the view
        return True

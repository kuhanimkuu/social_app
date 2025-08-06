from rest_framework import permissions

    #Custom permission to only allow owners of an object to edit or delete it. Others can only read.
class IsOwnerOrReadOnly(permissions.BasePermission):
    

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so always allow GET, HEAD, OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner of the object.
        return obj.uploader == request.user or obj.commenter == request.user
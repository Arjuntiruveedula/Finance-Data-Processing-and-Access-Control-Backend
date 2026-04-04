from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import Group, Permission
from core.permissions import IsAdminRole
from .roles_serializers import (
    RoleSerializer, RoleWriteSerializer,
    AssignPermissionsSerializer, RemovePermissionsSerializer,
    PermissionSerializer,
)


class RoleViewSet(viewsets.ModelViewSet):
    """
    Admin-only API for managing Roles (Django Groups) and their permissions.

    Endpoints:
      GET    /api/roles/                       → List all roles
      POST   /api/roles/                       → Create a new role
      GET    /api/roles/<id>/                  → Retrieve a role with its permissions
      PATCH  /api/roles/<id>/                  → Rename a role
      DELETE /api/roles/<id>/                  → Delete a role

      PATCH  /api/roles/<id>/permissions/      → Assign permissions to a role
      DELETE /api/roles/<id>/permissions/      → Remove permissions from a role
    """
    queryset = Group.objects.prefetch_related('permissions').all()
    permission_classes = [IsAuthenticated, IsAdminRole]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return RoleWriteSerializer
        return RoleSerializer

    @action(detail=True, methods=['patch'], url_path='permissions')
    def assign_permissions(self, request, pk=None):
        """
        PATCH /api/roles/<id>/permissions/
        Body: { "permission_ids": [1, 2, 3] }
        Adds the listed permissions to the role (does not remove existing ones).
        """
        group = self.get_object()
        serializer = AssignPermissionsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        perms = Permission.objects.filter(id__in=serializer.validated_data['permission_ids'])
        group.permissions.add(*perms)

        return Response(RoleSerializer(group).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['delete'], url_path='permissions/remove')
    def remove_permissions(self, request, pk=None):
        """
        DELETE /api/roles/<id>/permissions/remove/
        Body: { "permission_ids": [1, 2] }
        Removes the listed permissions from the role.
        """
        group = self.get_object()
        serializer = RemovePermissionsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        perms = Permission.objects.filter(id__in=serializer.validated_data['permission_ids'])
        group.permissions.remove(*perms)

        return Response(RoleSerializer(group).data, status=status.HTTP_200_OK)


class PermissionListView(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/roles/available-permissions/
    Lists all available Django permissions so the Admin knows what IDs to use
    when assigning permissions to roles.
    """
    queryset = Permission.objects.select_related('content_type').all()
    serializer_class = PermissionSerializer
    permission_classes = [IsAuthenticated, IsAdminRole]

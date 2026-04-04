from rest_framework import serializers
from django.contrib.auth.models import Group, Permission


class PermissionSerializer(serializers.ModelSerializer):
    """Serializer for a Django Permission object."""
    class Meta:
        model = Permission
        fields = ('id', 'name', 'codename', 'content_type')


class RoleSerializer(serializers.ModelSerializer):
    """
    Serializer for a Role (Django Group).
    Exposes the group's id, name, and the list of permissions assigned to it.
    """
    permissions = PermissionSerializer(many=True, read_only=True)

    class Meta:
        model = Group
        fields = ('id', 'name', 'permissions')


class RoleWriteSerializer(serializers.ModelSerializer):
    """Serializer for creating / renaming a Role (Group)."""
    class Meta:
        model = Group
        fields = ('id', 'name')


class AssignPermissionsSerializer(serializers.Serializer):
    """
    Accepts a list of permission IDs to assign to a role.
    Used for PATCH /api/roles/<id>/permissions/
    """
    permission_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False,
        help_text="List of Permission IDs to assign to this role."
    )

    def validate_permission_ids(self, value):
        existing_ids = set(Permission.objects.filter(id__in=value).values_list('id', flat=True))
        invalid = set(value) - existing_ids
        if invalid:
            raise serializers.ValidationError(f"Invalid permission IDs: {sorted(invalid)}")
        return value


class RemovePermissionsSerializer(serializers.Serializer):
    """
    Accepts a list of permission IDs to remove from a role.
    Used for DELETE /api/roles/<id>/permissions/
    """
    permission_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False,
        help_text="List of Permission IDs to remove from this role."
    )

from rest_framework import serializers
from django.contrib.auth.models import Group, Permission
from .models import CustomUser

VALID_ROLES = ['Admin', 'Analyst', 'Viewer']

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    role = serializers.SerializerMethodField()
    set_role = serializers.ChoiceField(choices=VALID_ROLES, write_only=True, required=False)

    class Meta:
        model = CustomUser
        fields = ('id', 'username', 'email', 'role', 'set_role', 'password', 'is_active')

    def get_role(self, obj):
        return obj.role

    def create(self, validated_data):
        role_name = validated_data.pop('set_role', 'Viewer')
        password = validated_data.pop('password')
        user = CustomUser.objects.create_user(password=password, **validated_data)
        group, _ = Group.objects.get_or_create(name=role_name)
        user.groups.set([group])
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()
    set_role = serializers.ChoiceField(choices=VALID_ROLES, write_only=True, required=False)

    class Meta:
        model = CustomUser
        fields = ('id', 'username', 'email', 'role', 'set_role', 'is_active')
        read_only_fields = ('id', 'username')

    def get_role(self, obj):
        return obj.role

    def update(self, instance, validated_data):
        role_name = validated_data.pop('set_role', None)
        instance = super().update(instance, validated_data)
        if role_name:
            group, _ = Group.objects.get_or_create(name=role_name)
            instance.groups.set([group])
        return instance


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

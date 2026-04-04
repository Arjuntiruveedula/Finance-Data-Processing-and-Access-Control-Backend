from rest_framework import serializers
from django.contrib.auth.models import Group
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

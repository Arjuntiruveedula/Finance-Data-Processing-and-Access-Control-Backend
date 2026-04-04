from rest_framework import serializers
from .models import FinancialRecord

class FinancialRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = FinancialRecord
        fields = ('id', 'user', 'amount', 'type', 'category', 'date', 'notes', 'is_deleted', 'created_at', 'updated_at')
        read_only_fields = ('user', 'is_deleted', 'created_at', 'updated_at')

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero.")
        return value

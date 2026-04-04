from django.db import models
from django.conf import settings

class FinancialRecord(models.Model):
    TYPE_CHOICES = (
        ('Income', 'Income'),
        ('Expense', 'Expense'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='financial_records')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    category = models.CharField(max_length=50) # Expected: Salary, Rent, Food, etc.
    date = models.DateField()
    notes = models.TextField(blank=True, null=True)
    
    # Soft delete field
    is_deleted = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['user', 'date']),
            models.Index(fields=['is_deleted']),
        ]
        verbose_name = "Financial Record"
        verbose_name_plural = "Financial Records"
        permissions = [
            # Dashboard access
            ('view_dashboard_summary', 'Can view dashboard summary'),
            ('view_dashboard_trends',  'Can view dashboard trends'),
            # Record-level granular access
            ('export_financialrecord', 'Can export financial records'),
            ('manage_own_financialrecord', 'Can manage own financial records only'),
            ('view_all_financialrecords', 'Can view financial records of all users'),
            ('approve_financialrecord', 'Can approve/reject financial records'),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.type} - {self.amount}"

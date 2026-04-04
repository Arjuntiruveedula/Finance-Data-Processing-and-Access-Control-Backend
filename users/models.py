from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    @property
    def role(self):
        if self.groups.exists():
            return self.groups.first().name
        return 'Viewer'

    class Meta:
        ordering = ['-date_joined']

    def __str__(self):
        return f"{self.username} - {self.role}"

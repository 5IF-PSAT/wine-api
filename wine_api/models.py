from django.db import models


class BaseEntity(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, editable=False, null=True, blank=True, serialize=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True, serialize=True)

    class Meta:
        abstract = True

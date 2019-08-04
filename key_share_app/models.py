from django.db import models
from django.contrib.auth.models import User

class Key(models.Model):
    # Data fields
    name = models.CharField(max_length=255)
    key = models.CharField(max_length=100)
    notes = models.CharField(max_length=500, null=True, blank=True)
    created = models.DateTimeField('created timestamp', auto_now_add=True, editable=False)
    last_updated = models.DateTimeField('last updated timestamp', auto_now=True, editable=False)
    redeemed = models.DateTimeField('redeemed timestamp', null=True, blank=True)

    # Relationship fields
    parent_key = models.ForeignKey(
        'Key', # Another instance of this object
        related_name='child_key',
        null=True, # Store blank as NULL
        blank=True, # Not required
        on_delete=models.CASCADE
    )
    created_by = models.ForeignKey(
        User, # Django User model
        related_name='submitted_keys',
        on_delete=models.CASCADE
    )
    updated_by = models.ForeignKey(
        User, # Django User model
        related_name='updated_keys',
        null=True, # Store blank as NULL
        blank=True, # Not required
        on_delete=models.CASCADE
    )
    redeemed_by = models.ForeignKey(
        User, # Django User model
        related_name='redeemed_keys',
        null=True, # Store blank as NULL
        blank=True, # Not required
        on_delete=models.CASCADE
    )

    def __str__(self):
        return self.name
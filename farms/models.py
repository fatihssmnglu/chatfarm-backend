from django.db import models


class Farm(models.Model):

    name = models.CharField(max_length=200)

    location = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
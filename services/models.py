from django.db import models


class ServiceCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    icon = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Service categories"
        ordering = ["name"]

    def __str__(self):
        return self.name

from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Publisher(models.Model):
    name = models.CharField(max_length=100)
    headquarter = models.CharField(max_length=100)
    registered_by = models.ForeignKey(User, on_delete=models.PROTECT)

    def __str__(self):
        return self.name

    @property
    def city(self) -> str:
        return self.headquarter.split(',')[0].strip()

    @property
    def country(self) -> str:
        return self.headquarter.split(',')[1].strip()


class Author(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Book(models.Model):
    title = models.CharField(max_length=100)
    price = models.PositiveIntegerField(null=True, blank=True)
    publisher = models.ForeignKey(Publisher, on_delete=models.CASCADE)
    authors = models.ManyToManyField(Author)
    is_on_sale = models.BooleanField(default=True)
    description = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    @property
    def name(self) -> str:
        return f'{self.title}  ({self.publisher.name})'

from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    email = models.EmailField(
        verbose_name='Email address',
        max_length=255,
        unique=True,
    )
    username = models.CharField(
        verbose_name='Username',
        max_length=255,
        unique=True
    )
    first_name = models.CharField(
        verbose_name='Name',
        max_length=150,
    )
    last_name = models.CharField(
        verbose_name='Last name',
        max_length=150
    )
    date_of_birth = models.DateField(
        verbose_name='Date of birth',
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name_plural = 'Users'
        verbose_name = 'User'

    def __str__(self):
        return f'User {self.username}'

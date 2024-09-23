from dj_rest_auth.registration.serializers import RegisterSerializer as DjRegisterSerializer
from dj_rest_auth.serializers import UserDetailsSerializer as DjUserDetailsSerializer
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from allauth.account.adapter import get_adapter
from allauth.account.utils import setup_user_email

from users.models import User


class RegisterSerializer(DjRegisterSerializer):
    """Override drf_rest_auth registration to include first_name and last_name."""
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)

    def get_cleaned_data(self):
        return {
            'username': self.validated_data.get('username', ''),
            'password1': self.validated_data.get('password1', ''),
            'email': self.validated_data.get('email', ''),
            'first_name': self.validated_data.get('first_name', ''),
            'last_name': self.validated_data.get('last_name', ''),
        }

    def save(self, request):
        adapter = get_adapter()
        user = adapter.new_user(request)
        self.cleaned_data = self.get_cleaned_data()

        user.first_name = self.cleaned_data.get('first_name', '')
        user.last_name = self.cleaned_data.get('last_name', '')

        user = adapter.save_user(request, user, self, commit=False)

        if "password1" in self.cleaned_data:
            try:
                adapter.clean_password(self.cleaned_data['password1'], user=user)
            except DjangoValidationError as exc:
                raise serializers.ValidationError(
                    detail=serializers.as_serializer_error(exc)
                )

        user.save()

        self.custom_signup(request, user)

        setup_user_email(request, user, [])

        return user


class UserSerializer(DjUserDetailsSerializer):
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'date_of_birth')
        read_only_fields = ('email',)

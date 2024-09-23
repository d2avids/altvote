from rest_framework import viewsets, permissions

from polls.models import Category
from polls.serializers import CategorySerializer


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = CategorySerializer

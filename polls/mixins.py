from rest_framework.mixins import ListModelMixin, CreateModelMixin
from rest_framework.viewsets import GenericViewSet


class ListCreateMixin(
    ListModelMixin,
    CreateModelMixin,
    GenericViewSet
):
    pass

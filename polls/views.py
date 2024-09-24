from django.db.models import Prefetch
from rest_framework import viewsets, permissions

from polls.models import Category, Poll, Option, PollCategory
from polls.serializers import CategorySerializer, PollSerializer


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = CategorySerializer


class PollViewSet(viewsets.ModelViewSet):
    queryset = Poll.objects.all().select_related('author').prefetch_related(
        Prefetch(
            'categories', 
            queryset=PollCategory.objects.select_related('category')
        ),
        Prefetch(
            'options',
            queryset=Option.objects.all()
        )
    )
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = PollSerializer

    def perform_create(self, serializer):
        author = self.request.user
        serializer.save(author=author)

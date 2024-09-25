from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, permissions

from polls.models import Category, Comment, Poll, SimpleVote, PollCategory
from polls.serializers import CategorySerializer, CommentSerializer, PollSerializer, SimpleVoteSerializer


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
        'options'
    )
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = PollSerializer

    def perform_create(self, serializer):
        author = self.request.user
        serializer.save(author=author)


class SimpleVoteViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = SimpleVoteSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update(
            {
                'poll': Poll.objects.get(pk=self.kwargs['poll_pk']),
                'author': self.request.user
            }
        )
        return context

    def get_queryset(self):
        return SimpleVote.objects.filter(poll_id=self.kwargs.get('poll_pk'))

    def perform_create(self, serializer):
        poll = get_object_or_404(Poll, pk=self.kwargs.get('poll_pk'))
        author = self.request.user
        serializer.save(author=author, poll=poll)


class CommentViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = CommentSerializer

    def get_queryset(self):
        return Comment.objects.filter(
            poll_id=self.kwargs.get('poll_pk')
        ).select_related('author')

    def perform_create(self, serializer):
        poll = get_object_or_404(Poll, pk=self.kwargs.get('poll_pk'))
        author = self.request.user
        serializer.save(author=author, poll=poll)

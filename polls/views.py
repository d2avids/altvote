from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action

from polls.mixins import ListCreateMixin
from polls.models import Category, Comment, Poll, SimpleVote, PollCategory, RankedVote
from polls.serializers import CategorySerializer, PollSerializer, SimpleVoteSerializer, \
    RankedVoteReadSerializer, RankedVoteWriteSerializer, CommentReadSerializer, CommentWriteSerializer


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

    @action(
        detail=True,
        methods=['DELETE'],
        url_path='users_simple_votes',
        permission_classes=(permissions.IsAuthenticated,)
    )
    def destroy_simple_votes(self, request, pk=None):
        """Deletes all User's Simple Votes for a given Poll."""
        SimpleVote.objects.filter(
            poll_id=pk, author=self.request.user
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['DELETE'],
        url_path='users_ranked_votes',
        permission_classes=(permissions.IsAuthenticated,)
    )
    def destroy_ranked_votes(self, request, pk=None):
        """Deletes all User's Ranked Votes for a given Poll."""
        RankedVote.objects.filter(
            poll_id=pk, author=self.request.user, is_preferential=False
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['DELETE'],
        url_path='users_preferential_votes',
        permission_classes=(permissions.IsAuthenticated,)
    )
    def destroy_preferential_votes(self, request, pk=None):
        """Deletes all User's Preferential Votes for a given Poll."""
        RankedVote.objects.filter(
            poll_id=pk, author=self.request.user, is_preferential=True
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SimpleVoteViewSet(ListCreateMixin):
    """Manages current user's Simple Votes."""
    serializer_class = SimpleVoteSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return SimpleVote.objects.filter(poll_id=self.kwargs.get('poll_pk'), author=self.request.user)

    def perform_create(self, serializer):
        poll = get_object_or_404(Poll, pk=self.kwargs.get('poll_pk'))
        author = self.request.user
        serializer.save(author=author, poll=poll)


class RankedVoteViewSet(ListCreateMixin):
    """Manages current user's Ranked and Preferential Votes."""
    permission_classes = (permissions.IsAuthenticated,)
    # TODO: filter is_preferential

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update(
            {
                'poll': Poll.objects.get(pk=self.kwargs['poll_pk']),
                'author': self.request.user,
            }
        )
        return context

    def get_serializer_class(self):
        if self.action == 'list':
            return RankedVoteReadSerializer
        return RankedVoteWriteSerializer

    def get_queryset(self):
        return RankedVote.objects.filter(poll_id=self.kwargs.get('poll_pk'), author=self.request.user)


class CommentViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)

    def get_serializer_class(self):
        if self.action == 'list':
            return CommentReadSerializer
        return CommentWriteSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({'poll_id': self.kwargs['poll_pk']})
        return context

    def get_queryset(self):
        return Comment.objects.filter(
            poll_id=self.kwargs.get('poll_pk'),
            parent__isnull=True
        ).select_related('author')

    def perform_create(self, serializer):
        poll = get_object_or_404(Poll, pk=self.kwargs.get('poll_pk'))
        author = self.request.user
        serializer.save(author=author, poll=poll)

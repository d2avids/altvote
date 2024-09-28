from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action

from polls.mixins import ListCreateMixin
from polls.models import Category, Comment, Poll, SimpleVote, PollCategory, RankedVote
from polls.serializers import CategorySerializer, PollSerializer, SimpleVoteSerializer, \
    RankedVoteReadSerializer, RankedVoteWriteSerializer, CommentReadSerializer, CommentWriteSerializer
from polls.tasks import on_like, on_dislike, on_ranked_votes, on_comment, on_simple_vote


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
        simple_votes = SimpleVote.objects.filter(
            poll_id=pk, author=self.request.user
        )
        for simple_vote in simple_votes:
            on_simple_vote.delay(option_pk=simple_vote.option.id, created=False)
        simple_votes.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['DELETE'],
        url_path='users_ranked_votes',
        permission_classes=(permissions.IsAuthenticated,)
    )
    def destroy_ranked_votes(self, request, pk=None):
        """Deletes all User's Ranked Votes for a given Poll."""
        ranked_votes = RankedVote.objects.filter(
            poll_id=pk, author=self.request.user, is_preferential=False
        )
        if ranked_votes:
            options_list = ranked_votes.values_list('option_id', 'points', flat=True)
            options_dict = {option[0]: option[1] for option in options_list}
            on_ranked_votes.delay(options_dict=options_dict, created=False, ranked=True)
        ranked_votes.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['DELETE'],
        url_path='users_preferential_votes',
        permission_classes=(permissions.IsAuthenticated,)
    )
    def destroy_preferential_votes(self, request, pk=None):
        """Deletes all User's Preferential Votes for a given Poll."""
        preferential_votes = RankedVote.objects.filter(
            poll_id=pk, author=self.request.user, is_preferential=True
        )
        if preferential_votes:
            options_list = preferential_votes.values_list('option_id', 'points', flat=True)
            options_dict = {option[0]: option[1] for option in options_list}
            on_ranked_votes.delay(options_dict=options_dict, created=False, ranked=False)
        preferential_votes.delete()
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
        poll_pk = self.kwargs.get('poll_pk')
        poll = get_object_or_404(Poll, pk=poll_pk)
        on_comment.delay(poll_pk=poll_pk, created=True)
        serializer.save(author=self.request.user, poll=poll)

    def perform_destroy(self, instance):
        on_comment.delay(poll_pk=self.kwargs.get('poll_pk'), created=False)
        instance.delete()

    @action(
        detail=True,
        methods=['POST'],
        url_path='likes',
        permission_classes=(permissions.IsAuthenticated,)
    )
    def likes(self, request, pk=None):
        poll_id = self.kwargs.get('poll_pk')
        get_object_or_404(Comment, pk=pk, poll_id=poll_id)
        on_like.delay(comment_pk=pk, user_pk=self.request.user.id)
        return Response(status=status.HTTP_201_CREATED)

    @action(
        detail=True,
        methods=['POST'],
        url_path='dislikes',
        permission_classes=(permissions.IsAuthenticated,)
    )
    def dislikes(self, request, pk=None):
        poll_id = self.kwargs.get('poll_pk')
        get_object_or_404(Comment, pk=pk, poll_id=poll_id)
        on_dislike.delay(comment_pk=pk, user_pk=self.request.user.id)
        return Response(status=status.HTTP_201_CREATED)

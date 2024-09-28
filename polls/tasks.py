from contextlib import suppress

from celery import shared_task
from django.core.exceptions import ObjectDoesNotExist

from polls.models import Comment, CommentLike, CommentDislike, Poll
from users.models import User


@shared_task
def on_like(comment_pk: int, user_pk: int):
    comment = Comment.objects.get(pk=comment_pk)
    user = User.objects.get(pk=user_pk)

    try:
        comment_like = CommentLike.objects.get(user=user, comment=comment)
        comment_like.delete()
        comment.likes_count -= 1
        comment.save()
    except CommentLike.DoesNotExist:

        with suppress(ObjectDoesNotExist):
            CommentDislike.objects.get(user=user, comment=comment).delete()

        CommentLike.objects.create(user=user, comment=comment)
        comment.likes_count += 1
        comment.save()


@shared_task
def on_dislike(comment_pk: int, user_pk: int):
    comment = Comment.objects.get(pk=comment_pk)
    user = User.objects.get(pk=user_pk)

    try:
        comment_dislike = CommentDislike.objects.get(user=user, comment=comment)
        comment_dislike.delete()
        comment.dislikes_count -= 1
        comment.save()
    except CommentDislike.DoesNotExist:

        with suppress(ObjectDoesNotExist):
            CommentLike.objects.get(user=user, comment=comment).delete()

        CommentDislike.objects.create(user=user, comment=comment)
        comment.dislikes_count += 1
        comment.save()


@shared_task
def on_new_comment(poll_pk: int):
    poll = Poll.objects.get(pk=poll_pk)
    poll.comments_count += 1
    poll.save()


@shared_task
def on_destroy_comment(poll_pk: int):
    poll = Poll.objects.get(pk=poll_pk)
    poll.comments_count -= 1
    poll.save()

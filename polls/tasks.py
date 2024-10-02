from contextlib import suppress
from typing import Dict

from celery import shared_task
from django.core.exceptions import ObjectDoesNotExist

from polls.models import Comment, CommentLike, CommentDislike, Poll, Option
from users.models import User


@shared_task
def on_simple_vote(option_pk: int, created: bool):
    option = Option.objects.get(pk=option_pk)
    if created:
        option.votes += 1
    else:
        option.votes -= 1
    option.save()


@shared_task
def on_ranked_votes(options_dict: Dict[int, int], created: bool, ranked: bool):
    options_to_update = []
    for option_pk, points in options_dict.items():
        option = Option.objects.get(pk=option_pk)

        if created:
            if ranked:
                option.ranked_points += points
            else:
                if not option.preferential_votes:
                    option.preferential_votes = {points: 1}
                else:
                    option.preferential_votes[points] = option.preferential_votes.get(points, 0) + 1

        else:
            if ranked:
                option.ranked_points -= points
            else:
                option.preferential_votes[points] -= 1

        options_to_update.append(option)
    Option.objects.bulk_update(
        options_to_update,
        ['ranked_points'] if ranked else ['preferential_votes']
    )


@shared_task
def on_like(comment_pk: int, user_pk: int):
    comment = Comment.objects.get(pk=comment_pk)
    user = User.objects.get(pk=user_pk)

    try:
        comment_like = CommentLike.objects.get(author=user, comment=comment)
        comment_like.delete()
        comment.likes_count -= 1
        comment.save()
    except CommentLike.DoesNotExist:

        with suppress(ObjectDoesNotExist):
            CommentDislike.objects.get(author=user, comment=comment).delete()

        CommentLike.objects.create(author=user, comment=comment)
        comment.likes_count += 1
        comment.save()


@shared_task
def on_dislike(comment_pk: int, user_pk: int):
    comment = Comment.objects.get(pk=comment_pk)
    user = User.objects.get(pk=user_pk)

    try:
        comment_dislike = CommentDislike.objects.get(author=user, comment=comment)
        comment_dislike.delete()
        comment.dislikes_count -= 1
        comment.save()
    except CommentDislike.DoesNotExist:

        with suppress(ObjectDoesNotExist):
            CommentLike.objects.get(author=user, comment=comment).delete()

        CommentDislike.objects.create(author=user, comment=comment)
        comment.dislikes_count += 1
        comment.save()


@shared_task
def on_comment(poll_pk: int, created: bool):
    poll = Poll.objects.get(pk=poll_pk)
    if created:
        poll.comments_count += 1
    else:
        poll.comments_count -= 1
    poll.save()

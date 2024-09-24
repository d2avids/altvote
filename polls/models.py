from django.db import models


class Category(models.Model):
    name = models.CharField(
        verbose_name='Category Name',
        max_length=60,
    )

    class Meta:
        verbose_name = 'Polls Category'
        verbose_name_plural = 'Polls Categories'

    def __str__(self) -> str:
        return self.name


class Poll(models.Model):
    author = models.ForeignKey(
        verbose_name='Author',
        on_delete=models.CASCADE,
        related_name='created_polls',
        to='users.User',
    )
    title = models.CharField(
        verbose_name='Title', 
        max_length=255,
    )
    description = models.TextField(
        verbose_name='Description',
        blank=True,
        null=True,
    )
    end_datetime = models.DateTimeField(
        verbose_name='Poll Deadline',
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(
        verbose_name='Created At',
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        verbose_name='Updated At',
        auto_now=True
    )
    is_confirmed = models.BooleanField(
        verbose_name='Confirmed',
        default=False
    )

    class Meta:
        verbose_name = 'Poll'
        verbose_name_plural = 'Polls'

    def __str__(self) -> str:
        return self.title


class PollCategory(models.Model):
    poll = models.ForeignKey(
        verbose_name='Poll',
        on_delete=models.CASCADE,
        related_name='categories',
        to='polls.Poll',
    )
    category = models.ForeignKey(
        verbose_name='Category',
        on_delete=models.CASCADE,
        related_name='polls',
        to='polls.Category'
    )


class Option(models.Model):
    poll = models.ForeignKey(
        verbose_name='Poll',
        on_delete=models.CASCADE,
        related_name='options',
        to='polls.Poll',
    )
    option = models.TextField(verbose_name='Option')
    image = models.ImageField(
        verbose_name='Image',
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = 'Poll Option'
        verbose_name_plural = 'Polls Options'

    def __str__(self) -> str:
        return f'{self.poll}: {self.option}'


class BaseVote(models.Model):
    author = models.ForeignKey(
        verbose_name='Author',
        on_delete=models.CASCADE,
        related_name='%(class)s',
        to='users.User',
    )
    # even though it is possible to access poll by option field,
    # duplicating poll field improves performance and simplifies querying
    poll = models.ForeignKey(
        verbose_name='Poll',
        on_delete=models.CASCADE,
        related_name='%(class)s',
        to='polls.Poll',
    )
    option = models.ForeignKey(
        verbose_name='Option',
        on_delete=models.CASCADE,
        related_name='%(class)s',
        to='polls.Option'
    )
    created_at = models.DateTimeField(
        verbose_name='Created at',
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        verbose_name='Updated at',
        auto_now=True
    )

    class Meta:
        abstract = True


class SimpleVote(BaseVote):

    class Meta:
        verbose_name = 'Simple Vote'
        verbose_name_plural = 'Simple Votes'

    def __str__(self) -> str:
        return f'{self.author} on {self.poll} votes {self.option}'


class RankedVote(BaseVote):
    points = models.IntegerField(
        verbose_name='Points'
    )

    class Meta:
        verbose_name = 'Ranked Vote'
        verbose_name_plural = 'Ranked Votes'

    def __str__(self) -> str:
        return f'{self.author} on {self.poll} ranks {self.option} at {self.points}'


class Comment(models.Model):
    author = models.ForeignKey(
        verbose_name='Author',
        on_delete=models.CASCADE,
        related_name='comments',
        to='users.User',
    )
    poll = models.ForeignKey(
        verbose_name='Poll',
        on_delete=models.CASCADE,
        related_name='comments',
        to='polls.Poll'
    )
    content = models.TextField(verbose_name='Content')
    created_at = models.DateTimeField(
        verbose_name='Created At',
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        verbose_name='Updated At',
        auto_now=True
    )

    class Meta:
        verbose_name = 'Comment'
        verbose_name_plural = 'Comments'

    def __str__(self) -> str:
        return f'{self.author} comments on {self.poll}: "{self.content[:20]}..."'



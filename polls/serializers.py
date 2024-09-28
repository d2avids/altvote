from rest_framework import serializers
from drf_extra_fields.fields import Base64ImageField
from polls.models import Category, Comment, Option, Poll, PollCategory, SimpleVote, RankedVote
from polls.utils import poll_end_datetime_passed
from users.models import User


class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name')


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name')


class OptionSerializer(serializers.ModelSerializer):
    image = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = Option
        fields = ('id', 'option', 'image')


class PollSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)
    categories = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), many=True
    )
    options = OptionSerializer(many=True)

    class Meta:
        model = Poll
        fields = (
            'id', 
            'author', 
            'title', 
            'description', 
            'end_datetime', 
            'categories',
            'options',
            'comments_count',
            'created_at', 
            'updated_at', 
            'is_confirmed'
        )
        read_only_fields = (
            'comments_count',
            'created_at', 
            'updated_at', 
            'is_confirmed'
        )

    def to_representation(self, instance):
        repr = super().to_representation(instance)
        
        categories_slugs = [poll_category.category.name for poll_category in instance.categories.all()]
        
        repr['categories'] = categories_slugs
        return repr

    def create(self, validated_data):
        categories = validated_data.pop('categories')
        options = validated_data.pop('options')

        poll = super().create(validated_data)

        poll_categories = [PollCategory(poll=poll, category=category) for category in categories]
        PollCategory.objects.bulk_create(poll_categories)

        poll_options = [Option(poll=poll, **option_kwargs) for option_kwargs in options]
        Option.objects.bulk_create(poll_options)

        return poll

    def update(self, instance, validated_data):
        instance.categories.all().delete()
        instance.options.all().delete()
        categories = validated_data.pop('categories')
        options = validated_data.pop('options')

        poll_categories = [PollCategory(poll=instance, category=category) for category in categories]
        PollCategory.objects.bulk_create(poll_categories)

        poll_options = [Option(poll=instance, **option_kwargs) for option_kwargs in options]
        Option.objects.bulk_create(poll_options)

        for key, val in validated_data.items():
            setattr(instance, key, val)
        instance.save()
        return instance


class SimpleVoteSerializer(serializers.ModelSerializer):
    option = serializers.PrimaryKeyRelatedField(queryset=Option.objects.all())

    class Meta:
        model = SimpleVote
        fields = ('id', 'option', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')

    def validate_option(self, option):
        poll = self.instance.poll if self.instance else self.context['poll']

        if option.poll != poll:
            raise serializers.ValidationError('This option is not available for this poll.')

        return option

    def validate(self, attrs):
        poll = self.context['poll']

        if poll_end_datetime_passed(poll):
            raise serializers.ValidationError({'error': 'The poll has been finished.'})

        if SimpleVote.objects.filter(
                poll=poll, author=self.context['author']
        ).exists():
            raise serializers.ValidationError({'error': 'You have already voted for this poll.'})

        return attrs


class RankedVoteOptionSerializer(serializers.ModelSerializer):
    option = serializers.PrimaryKeyRelatedField(queryset=Option.objects.all())
    points = serializers.IntegerField()

    class Meta:
        model = RankedVote
        fields = ('option', 'points', 'is_preferential', 'created_at', 'updated_at')
        read_only_fields = ('created_at', 'updated_at')


class RankedVoteReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = RankedVote
        fields = ('id', 'option', 'points', 'created_at', 'updated_at', 'is_preferential')


class RankedVoteWriteSerializer(serializers.Serializer):
    votes = RankedVoteOptionSerializer(many=True)
    is_preferential = serializers.BooleanField()

    def validate(self, attrs):
        poll = self.context['poll']

        if poll_end_datetime_passed(poll):
            raise serializers.ValidationError({'error': 'The poll has been finished.'})

        poll_options = list(poll.options.all())

        is_preferential = attrs['is_preferential']
        if is_preferential:
            preferential_points = list(range(1, len(poll_options) + 1))

        for ranked_option in attrs['votes']:
            option = ranked_option.get('option')
            points = ranked_option.get('points')

            if RankedVote.objects.filter(
                    poll=poll,
                    author=self.context['author'],
                    option=option,
                    is_preferential=is_preferential
            ).exists():
                raise serializers.ValidationError({'error': 'You have already voted for this option.'})

            if option not in poll_options:
                raise serializers.ValidationError(
                    {'options': f'The {option.id} option is duplicated or not available for this poll.'}
                )
            poll_options.remove(option)

            if is_preferential:
                if points not in preferential_points:
                    raise serializers.ValidationError(
                        {
                            'options': f'The {points} points value for {option.id} '
                                       f'option is duplicated or not available.'
                        }
                    )
                preferential_points.remove(points)

        if poll_options:
            raise serializers.ValidationError(
                {'options': 'Not all available options are provided in the vote for this poll.'}
            )

        return attrs

    def create(self, validated_data):
        poll = self.context['poll']
        author = self.context['author']
        is_preferential = self.validated_data['is_preferential']

        votes = [
            RankedVote(
                poll=poll,
                author=author,
                option=vote_data['option'],
                points=vote_data['points'],
                is_preferential=is_preferential,
            )
            for vote_data in validated_data['votes']
        ]
        RankedVote.objects.bulk_create(votes)

        return {
            'votes': votes,
            'is_preferential': is_preferential
        }


class CommentReadSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)
    replies = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = (
            'id',
            'author',
            'parent',
            'content',
            'likes_count',
            'dislikes_count',
            'created_at',
            'updated_at',
            'replies'
        )

    def get_replies(self, obj):
        replies = obj.replies.all()
        return CommentReadSerializer(replies, many=True).data


class CommentWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = (
            'id', 'parent', 'content', 'likes_count', 'dislikes_count', 'created_at', 'updated_at'
        )
        read_only_fields = (
            'id', 'created_at', 'updated_at', 'likes_count', 'dislikes_count'
        )

    def validate(self, attrs):
        poll_id = int(self.context['poll_id'])

        if attrs.get('parent'):
            if attrs['parent'].poll_id != poll_id:
                raise serializers.ValidationError('Parent comment must belong to the same poll.')

            if attrs['parent'].parent:
                raise serializers.ValidationError('Child comment must only belong to a top-level comment.')

        return attrs

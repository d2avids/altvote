from rest_framework import serializers
from drf_extra_fields.fields import Base64ImageField
from polls.models import Category, Comment, Option, Poll, PollCategory, SimpleVote
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
    image = Base64ImageField()

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
            'created_at', 
            'updated_at', 
            'is_confirmed'
        )
        read_only_fields = (
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
        fields = ('id', 'author', 'option', 'created_at', 'updated_at')
        read_only_fields = ('id', 'author', 'created_at', 'updated_at')

    def validate_option(self, option):
        poll = self.instance.poll if self.instance else self.context['poll']

        if option.poll != poll:
            raise serializers.ValidationError('This option is not available for this poll.')

        return option

class CommentSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ('id', 'author', 'content', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')

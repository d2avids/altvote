from django.urls import path, include
from rest_framework.routers import SimpleRouter

from polls.views import CategoryViewSet, CommentViewSet, PollViewSet, SimpleVoteViewSet


router_v1 = SimpleRouter()
router_v1.register(r'categories', CategoryViewSet, 'category')
router_v1.register(r'polls', PollViewSet, 'poll')
router_v1.register(r'polls/(?P<poll_pk>\d+)/simple_votes', SimpleVoteViewSet, 'simple_vote')
router_v1.register(r'polls/(?P<poll_pk>\d+)/comments', CommentViewSet, 'comment')


urlpatterns = [
    path('', include(router_v1.urls))
]

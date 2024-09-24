from django.urls import path, include
from rest_framework.routers import SimpleRouter

from polls.views import CategoryViewSet, PollViewSet


router_v1 = SimpleRouter()
router_v1.register(r'categories', CategoryViewSet, 'category')
router_v1.register(r'polls', PollViewSet, 'poll')

urlpatterns = [
    path('', include(router_v1.urls))
]

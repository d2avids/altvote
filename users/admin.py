from django.contrib.auth.models import Group
from django.contrib.sites.models import Site
from django.contrib import admin
from django.conf import settings
from rest_framework.authtoken.models import TokenProxy

from users.models import User


admin.AdminSite.site_header = 'AltVote Administration'
admin.AdminSite.site_title = 'AltVote Administration'
admin.AdminSite.index_title = 'AltVote'

if not settings.DEBUG:
    admin.site.unregister(TokenProxy)
 
admin.site.unregister(Group)
admin.site.unregister(Site)


@admin.register(User)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name')
    search_fields = ('username', 'email', 'first_name', 'last_name')

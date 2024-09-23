from users.models import User
from django.contrib import admin


@admin.register(User)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name')
    search_fields = ('username', 'email', 'first_name', 'last_name')


admin.AdminSite.site_header = 'AltVote Administration'
admin.AdminSite.site_title = 'AltVote Administration'
admin.AdminSite.index_title = 'AltVote'
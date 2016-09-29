from django.contrib import admin
from .models import Feed,Activity,Notification,Profile
# Register your models here.

class FeedModelAdmin(admin.ModelAdmin):
    list_display = ["post","user", "date", "likes","comments"]
    list_display_links = ["post"]

    search_fields = ["post", "user","likes","comments"]

    class Meta:
        model = Feed

class ActivityModelAdmin(admin.ModelAdmin):
    list_display = ["user","activity_type", "date", "feed"]
    list_display_links = ["user","date"]

    search_fields = ["feed", "user","date"]

    class Meta:
        model = Activity

class NotificationModelAdmin(admin.ModelAdmin):
    list_display = ["from_user","to_user", "date", "feed","is_read"]
    list_display_links = ["feed"]

    search_fields = ["feed", "from_user","to_user","date"]

    class Meta:
        model = Notification

class ProfileModelAdmin(admin.ModelAdmin):
    list_display = ["user", "location", "url","job_title","get_picture","follow"]
    list_display_links = ["user"]

    search_fields = ["user","location","job_title"]

    class Meta:
        model = Profile


admin.site.register(Feed,FeedModelAdmin)
admin.site.register(Activity,ActivityModelAdmin)
admin.site.register(Notification,NotificationModelAdmin)
admin.site.register(Profile,ProfileModelAdmin)
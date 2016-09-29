import urllib
import hashlib
import os.path

from django.db import models
from django.contrib.auth.models import User

from django.utils.html import escape
from django.db.models.signals import post_save
from django.conf import settings
import bleach

#####################
#       Activity
#####################
class Activity(models.Model):
    LIKE = 'L'
    ACTIVITY_TYPES = ((LIKE, 'Like'),)

    user = models.ForeignKey(User)
    activity_type = models.CharField(max_length=1, choices=ACTIVITY_TYPES)
    date = models.DateTimeField(auto_now_add=True)
    feed = models.IntegerField(null=True, blank=True)

    class Meta:
        verbose_name = 'Activity'
        verbose_name_plural = 'Activities'

    def __unicode__(self):
        return self.activity_type
#####################
#       Notification
#####################
class Notification(models.Model):
    LIKED = 'L'
    COMMENTED = 'C'
    NOTIFICATION_TYPES = ((LIKED, 'Liked'),(COMMENTED, 'Commented'),)

    _LIKED_TEMPLATE = u'<a href="/{0}/">{1}</a> liked your post: <a href="/feeds/{2}/">{3}</a>'
    _COMMENTED_TEMPLATE = u'<a href="/{0}/">{1}</a> commented on your post: <a href="/feeds/{2}/">{3}</a>'

    from_user = models.ForeignKey(User, related_name='+')
    to_user = models.ForeignKey(User, related_name='+')
    date = models.DateTimeField(auto_now_add=True)
    feed = models.ForeignKey('Feed', null=True, blank=True)

    notification_type = models.CharField(max_length=1, choices=NOTIFICATION_TYPES)
    is_read = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        ordering = ('-date',)

    def __unicode__(self):
        if self.notification_type == self.LIKED:
            return self._LIKED_TEMPLATE.format(
                escape(self.from_user.username),
                escape(self.from_user.profile.get_screen_name()),
                self.feed.pk,
                escape(self.get_summary(self.feed.post))
                )
        elif self.notification_type == self.COMMENTED:
            return self._COMMENTED_TEMPLATE.format(
                escape(self.from_user.username),
                escape(self.from_user.profile.get_screen_name()),
                self.feed.pk,
                escape(self.get_summary(self.feed.post))
                )
        else:
            return 'Ooops! Something went wrong.'

    def get_summary(self, value):
        summary_size = 50
        if len(value) > summary_size:
            return u'{0}...'.format(value[:summary_size])

        else:
            return value
#####################
#       Profile
#####################
class Profile(models.Model):
    user = models.OneToOneField(User)
    location = models.CharField(max_length=50, null=True, blank=True)
    url = models.CharField(max_length=50, null=True, blank=True)
    job_title = models.CharField(max_length=50, null=True, blank=True)
    follow = models.BooleanField(default=False)
    class Meta:
        db_table = 'auth_profile'

    def get_url(self):
        url = self.url
        if "http://" not in self.url and "https://" not in self.url and len(self.url) > 0:
            url = "http://" + str(self.url)
        return url

    def get_picture(self):
        no_picture = 'http://www.gudaak.com/uploads/user/small/avatar.png'
        try:
            filename = settings.MEDIA_ROOT + '/profile_pictures/' + self.user.username + '.jpg'
            picture_url = settings.MEDIA_URL + 'profile_pictures/' + self.user.username + '.jpg'
            if os.path.isfile(filename):
                return picture_url
            else:
                gravatar_url = u'http://www.gravatar.com/avatar/{0}?{1}'.format(
                    hashlib.md5(self.user.email.lower()).hexdigest(),
                    urllib.urlencode({'d': no_picture, 's': '256'})
                    )
                return gravatar_url

        except (Exception) as e:
            return no_picture

    def get_screen_name(self):
        try:
            if self.user.get_full_name():
                return self.user.get_full_name()
            else:
                return self.user.username
        except:
            return self.user.username

    def notify_liked(self, feed):
        if self.user != feed.user:
            Notification(notification_type=Notification.LIKED,from_user=self.user, to_user=feed.user,feed=feed).save()

    def unotify_liked(self, feed):
        if self.user != feed.user:
            Notification.objects.filter(notification_type=Notification.LIKED,from_user=self.user, to_user=feed.user,feed=feed).delete()

    def notify_commented(self, feed):
        if self.user != feed.user:
            Notification(notification_type=Notification.COMMENTED,from_user=self.user, to_user=feed.user,feed=feed).save()


def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()
post_save.connect(create_user_profile, sender=User)
post_save.connect(save_user_profile, sender=User)
#####################
#       Feed
#####################
class Feed(models.Model):
    user = models.ForeignKey(User)
    date = models.DateTimeField(auto_now_add=True)
    post = models.TextField(max_length=250)
    parent = models.ForeignKey('Feed', null=True, blank=True)
    likes = models.IntegerField(default=0)
    comments = models.IntegerField(default=0)

    class Meta:
        verbose_name = 'Feed'
        verbose_name_plural = 'Feeds'
        ordering = ('-date',)

    def __unicode__(self):
        return self.post

    @staticmethod
    def get_feeds(from_feed=None):
        if from_feed is not None:
            feeds = Feed.objects.filter(user__profile__follow=True,parent=None,id__lte=from_feed)
        else:
            feeds = Feed.objects.filter(user__profile__follow=True,parent=None)
        return feeds

    @staticmethod
    def get_feeds_after(feed):
        feeds = Feed.objects.filter(parent=None, id__gt=feed)
        return feeds

    def get_comments(self):
        return Feed.objects.filter(parent=self).order_by('date')

    def calculate_likes(self):
        likes = Activity.objects.filter(activity_type=Activity.LIKE,feed=self.pk).count()
        self.likes = likes
        self.save()
        return self.likes

    def get_likes(self):
        likes = Activity.objects.filter(activity_type=Activity.LIKE,feed=self.pk)
        return likes

    def get_likers(self):
        likes = self.get_likes()
        likers = []
        for like in likes:
            likers.append(like.user)
        return likers

    def calculate_comments(self):
        self.comments = Feed.objects.filter(parent=self).count()
        self.save()
        return self.comments

    def comment(self, user, post):
        feed_comment = Feed(user=user, post=post, parent=self)
        feed_comment.save()
        self.comments = Feed.objects.filter(parent=self).count()
        self.save()
        return feed_comment

    def linkfy_post(self):
        return bleach.linkify(escape(self.post))


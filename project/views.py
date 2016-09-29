import os
from PIL import Image

from django.db.models import Q

from django.contrib.auth.models import User
from django.contrib import messages

from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from .decorators import ajax_required

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from django.conf import settings as django_settings

from django.template.loader import render_to_string
from django.template.context_processors import csrf
from django.http import HttpResponse, HttpResponseBadRequest,HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404

from .models import Notification, Feed,Activity,Profile
from .forms import ProfileForm, ChangePasswordForm,SignUpForm

FEEDS_NUM_PAGES = 50

def home(request):
    if request.user.is_authenticated():
        return feeds(request)
    else:
        return render(request, 'project/cover.html')

@login_required
def network(request):
    users_list = User.objects.filter(is_active=True, profile__follow=True).order_by('username')
    paginator = Paginator(users_list, 100)
    page = request.GET.get('page')
    try:
        users = paginator.page(page)
    except PageNotAnInteger:
        users = paginator.page(1)
    except EmptyPage:
        users = paginator.page(paginator.num_pages)
    return render(request, 'project/network.html', {'users': users})

@login_required
def profile(request, username):
    page_user = get_object_or_404(User, username=username)
    all_feeds = Feed.get_feeds().filter(user=page_user)
    paginator = Paginator(all_feeds, FEEDS_NUM_PAGES)
    feeds = paginator.page(1)
    from_feed = -1
    if feeds:
        from_feed = feeds[0].id
    return render(request, 'project/profile.html', {
        'page_user': page_user,
        'feeds': feeds,
        'from_feed': from_feed,
        'page': 1
        })
@login_required
def follow(request, user_id):
    user = get_object_or_404(Profile, pk=user_id)
    page_user = get_object_or_404(User, pk=user_id)
    try:
        if user.follow:
            user.follow = False
        else:
            user.follow = True
        user.save()
        all_feeds = Feed.get_feeds().filter(user=page_user)
        paginator = Paginator(all_feeds, FEEDS_NUM_PAGES)
        feeds = paginator.page(1)
        from_feed = -1
        if feeds:
            from_feed = feeds[0].id
    except (KeyError, Profile.DoesNotExist):
        return render(request, 'project/profile.html', {
            'page_user': page_user,
            'error_message': "You Did Not Select A Valid Song",
        })
    else:
        return render(request, 'project/profile.html', {
            'page_user': page_user,
            'feeds': feeds,
            'from_feed': from_feed,
            'page': 1
        })

@login_required
def settings(request):
    user = request.user
    if request.method == 'POST':
        form = ProfileForm(request.POST)
        if form.is_valid():
            user.first_name = form.cleaned_data.get('first_name')
            user.last_name = form.cleaned_data.get('last_name')
            user.profile.job_title = form.cleaned_data.get('job_title')
            user.email = form.cleaned_data.get('email')
            user.profile.url = form.cleaned_data.get('url')
            user.profile.location = form.cleaned_data.get('location')
            user.save()
            messages.add_message(request,messages.SUCCESS,'Your profile was successfully edited.')

    else:
        form = ProfileForm(instance=user, initial={
            'job_title': user.profile.job_title,
            'url': user.profile.url,
            'location': user.profile.location
            })
    return render(request, 'project/settings.html', {'form': form})

@login_required
def picture(request):
    uploaded_picture = False
    try:
        if request.GET.get('upload_picture') == 'uploaded':
            uploaded_picture = True

    except (Exception) as e:
        pass

    return render(request, 'project/picture.html',{'uploaded_picture': uploaded_picture})

@login_required
def password(request):
    user = request.user
    if request.method == 'POST':
        form = ChangePasswordForm(request.POST)
        if form.is_valid():
            new_password = form.cleaned_data.get('new_password')
            user.set_password(new_password)
            user.save()
            messages.add_message(request, messages.SUCCESS,
                                 'Your password was successfully changed.')

    else:
        form = ChangePasswordForm(instance=user)

    return render(request, 'project/password.html', {'form': form})

@login_required
def upload_picture(request):
    try:
        profile_pictures = django_settings.MEDIA_ROOT + '/profile_pictures/'
        if not os.path.exists(profile_pictures):
            os.makedirs(profile_pictures)
        f = request.FILES['picture']
        filename = profile_pictures + request.user.username + '_tmp.jpg'
        with open(filename, 'wb+') as destination:
            for chunk in f.chunks():
                destination.write(chunk)
        im = Image.open(filename)
        width, height = im.size
        if width > 350:
            new_width = 350
            new_height = (height * 350) / width
            new_size = new_width, new_height
            im.thumbnail(new_size, Image.ANTIALIAS)
            im.save(filename)

        return redirect('/settings/picture/?upload_picture=uploaded')


    except (Exception) as e:
        pass
        return redirect('/settings/picture/')

@login_required
def save_uploaded_picture(request):
    try:
        x = int(request.POST.get('x'))
        y = int(request.POST.get('y'))
        w = int(request.POST.get('w'))
        h = int(request.POST.get('h'))
        tmp_filename = django_settings.MEDIA_ROOT + '/profile_pictures/' + request.user.username + '_tmp.jpg'
        filename = django_settings.MEDIA_ROOT + '/profile_pictures/' + request.user.username + '.jpg'
        im = Image.open(tmp_filename)
        cropped_im = im.crop((x, y, w+x, h+y))
        cropped_im.thumbnail((200, 200), Image.ANTIALIAS)
        cropped_im.save(filename)
        os.remove(tmp_filename)


    except (Exception) as e:
        pass

    return redirect('/settings/picture/')

###############################################
@login_required
def notifications(request):
    user = request.user
    notifications = Notification.objects.filter(to_user=user, from_user__profile__follow=True)
    unread = Notification.objects.filter(to_user=user, from_user__profile__follow=True, is_read=False)
    for notification in unread:
        notification.is_read = True
        notification.save()

    return render(request, 'project/notifications.html',{'notifications': notifications})

###############################################

def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if not form.is_valid():
            return render(request, 'project/signup.html',{'form': form})

        else:
            username = form.cleaned_data.get('username')
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password')
            User.objects.create_user(username=username, password=password,email=email)
            user = authenticate(username=username, password=password)
            login(request, user)
            welcome_post = u'{0} has joined the network.'.format(user.username,user.username)
            feed = Feed(user=user, post=welcome_post)
            feed.save()
            return redirect('/')

    else:
        return render(request, 'project/signup.html',{'form': SignUpForm()})
###############################################

@login_required
def feeds(request):
    all_feeds = Feed.objects.filter(user__profile__follow=True)
    all_feeds = Feed.get_feeds()
    paginator = Paginator(all_feeds, FEEDS_NUM_PAGES)
    feeds = paginator.page(1)
    from_feed = -1
    if feeds:
        from_feed = feeds[0].id
    return render(request, 'project/feeds.html', {
        'feeds': feeds,
        'from_feed': from_feed,
        'page': 1,
        })

@login_required
def feed(request, pk):
    feed = get_object_or_404(Feed, pk=pk)
    return render(request, 'project/feed.html', {'feed': feed})

@login_required
@ajax_required
def load(request):
    from_feed = request.GET.get('from_feed')
    page = request.GET.get('page')
    feed_source = request.GET.get('feed_source')
    all_feeds = Feed.get_feeds(from_feed)
    if feed_source != 'all':
        all_feeds = all_feeds.filter(user__id=feed_source)
    paginator = Paginator(all_feeds, FEEDS_NUM_PAGES)
    try:
        feeds = paginator.page(page)
    except PageNotAnInteger:
        return HttpResponseBadRequest()
    except EmptyPage:
        feeds = []
    html = u''
    csrf_token = csrf(request)['csrf_token']
    for feed in feeds:
        html = u'{0}{1}'.format(html,render_to_string('project/partial_feed.html',{'feed': feed,'user': request.user,'csrf_token': csrf_token}))
    return HttpResponse(html)

def _html_feeds(last_feed, user, csrf_token, feed_source='all'):
    feeds = Feed.get_feeds_after(last_feed)
    if feed_source != 'all':
        feeds = feeds.filter(user__id=feed_source)
    html = u''
    for feed in feeds:
        html = u'{0}{1}'.format(html,render_to_string('project/partial_feed.html',{'feed': feed,'user': user,'csrf_token': csrf_token}))
    return html

@login_required
@ajax_required
def post(request):
    last_feed = request.POST.get('last_feed')
    user = request.user
    csrf_token = csrf(request)['csrf_token']
    feed = Feed()
    feed.user = user
    post = request.POST['post']
    post = post.strip()
    if len(post) > 0:
        feed.post = post[:250]
        feed.save()
    html = _html_feeds(last_feed, user, csrf_token)
    return HttpResponse(html)

@login_required
@ajax_required
def like(request):
    feed_id = request.POST['feed']
    feed = Feed.objects.get(pk=feed_id)
    user = request.user
    like = Activity.objects.filter(activity_type=Activity.LIKE, feed=feed_id,user=user)
    if like:
        user.profile.unotify_liked(feed)
        like.delete()

    else:
        like = Activity(activity_type=Activity.LIKE, feed=feed_id, user=user)
        like.save()
        user.profile.notify_liked(feed)

    return HttpResponse(feed.calculate_likes())

@login_required
@ajax_required
def comment(request):
    if request.method == 'POST':
        feed_id = request.POST['feed']
        feed = Feed.objects.get(pk=feed_id)
        post = request.POST['post']
        post = post.strip()
        if len(post) > 0:
            post = post[:250]
            user = request.user
            feed.comment(user=user, post=post)
            user.profile.notify_commented(feed)
            user.profile.notify_also_commented(feed)
        return render(request, 'project/partial_feed_comments.html',
                      {'feed': feed})

    else:
        feed_id = request.GET.get('feed')
        feed = Feed.objects.get(pk=feed_id)
        return render(request, 'project/partial_feed_comments.html',
                      {'feed': feed})

@login_required
@ajax_required
def remove(request):
    try:
        feed_id = request.POST.get('feed')
        feed = Feed.objects.get(pk=feed_id)
        if feed.user == request.user:
            likes = feed.get_likes()
            parent = feed.parent
            for like in likes:
                like.delete()
            feed.delete()
            if parent:
                parent.calculate_comments()
            return HttpResponse()
        else:
            return HttpResponseForbidden()
    except (Exception) as e:
        return HttpResponseBadRequest()
##############################################
@login_required
def search(request):
    if 'q' in request.GET:
        querystring = request.GET.get('q').strip()
        if len(querystring) == 0:
            return redirect('/search/')
        try:
            search_type = request.GET.get('type')
            if search_type not in ['feed', 'users']:
                search_type = 'feed'

        except (Exception) as e:
            search_type = 'feed'

        count = {}
        results = {}
        results['feed'] = Feed.objects.filter(post__icontains=querystring,parent=None)

        results['users'] = User.objects.filter(
            Q(username__icontains=querystring) | Q(
                first_name__icontains=querystring) | Q(
                    last_name__icontains=querystring))
        count['feed'] = results['feed'].count()

        count['users'] = results['users'].count()

        return render(request, 'project/results.html', {
            'hide_search': True,
            'querystring': querystring,
            'active': search_type,
            'count': count,
            'results': results[search_type],
        })
    else:
        return render(request, 'project/search.html', {'hide_search': True})


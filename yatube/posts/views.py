from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from yatube.settings import PAGE_CAPACITY

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post
from .utils import get_page_obj

User = get_user_model()


@cache_page(20, key_prefix='index_page')
def index(request):
    template = 'posts/index.html'
    post_list = Post.objects.all()
    page_obj = get_page_obj(request, post_list, PAGE_CAPACITY)
    title = 'Последние обновления на сайте'
    index = True
    context = {
        'index': index,
        'title': title,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def group_posts(request, slug):
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    page_obj = get_page_obj(request, post_list, PAGE_CAPACITY)
    title = 'Записи сообщества ' + group.title
    context = {
        'title': title,
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def profile(request, username):
    template = 'posts/profile.html'

    this_user = get_object_or_404(User, username=username)
    post_list = this_user.posts.all()
    page_obj = get_page_obj(request, post_list, PAGE_CAPACITY)

    post_amount = this_user.posts.count()
    title = 'Профайл пользователя ' + this_user.get_username()

    if request.user.is_authenticated:
        following = Follow.objects.filter(
            user=request.user,
            author=get_object_or_404(User, username=username)
        ).exists()
    else:
        following = False

    context = {
        'title': title,
        'this_user': this_user,
        'page_obj': page_obj,
        'post_amount': post_amount,
        'following': following,
    }
    return render(request, template, context)


def post_detail(request, post_id):
    template = 'posts/post_detail.html'

    this_post = get_object_or_404(Post, id=post_id)
    title = 'Пост "' + this_post.text[:30] + '..."'

    this_author = this_post.author.username
    this_user = get_object_or_404(User, username=this_author)
    post_amount = this_user.posts.count()

    comments_list = this_post.comments.all()
    comment_form = CommentForm()

    context = {
        'title': title,
        'post_amount': post_amount,
        'post': this_post,
        'comments': comments_list,
        'form': comment_form,
    }
    return render(request, template, context)


@login_required
def post_create(request):
    template = 'posts/create_post.html'

    form = PostForm(
        request.POST or None,
        files=request.FILES or None
    )
    if form.is_valid():
        new_post = form.save(commit=False)
        new_post.author = request.user
        new_post.save()
        return redirect('posts:profile', request.user.username)

    context = {
        'form': form,
    }
    return render(request, template, context)


@login_required
def post_edit(request, post_id):
    this_post = get_object_or_404(Post, id=post_id)

    if request.user.username == this_post.author.username:
        form = PostForm(
            request.POST or None,
            files=request.FILES or None,
            instance=this_post
        )
        if form.is_valid():
            form.save()
            return redirect('posts:post_detail', post_id)

        template = 'posts/create_post.html'
        is_edit = True
        context = {
            'form': form,
            'is_edit': is_edit,
        }
        return render(request, template, context)

    return redirect('posts:post_detail', post_id)


@login_required
def add_comment(request, post_id):
    form = CommentForm(request.POST or None)

    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = get_object_or_404(Post, id=post_id)
        comment.save()

    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    template = 'posts/index.html'
    post_list = Post.objects.filter(author__following__user=request.user)
    page_obj = get_page_obj(request, post_list, PAGE_CAPACITY)
    title = 'Последние обновления в ленте подписок'
    follow = True
    context = {
        'title': title,
        'page_obj': page_obj,
        'follow': follow,
    }
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user != author:
        Follow.objects.get_or_create(
            user=request.user,
            author=author
        )
    return redirect('posts:profile', username)


@login_required
def profile_unfollow(request, username):
    Follow.objects.filter(
        user=request.user,
        author=get_object_or_404(User, username=username)
    ).delete()
    return redirect('posts:profile', username)

import operator

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User


def get_page_obj(request, posts):
    """
    Paginaror. Функция для оптимизации формата кода.
    """
    paginator = Paginator(posts, settings.RECORDS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj


@cache_page(20, key_prefix="index_page")
def index(request):
    """
    Главная страница сайта. Возвращает последние 10 постов сообществ.
    """
    posts = Post.objects.select_related("author", "group")
    context = {
        'page_obj': get_page_obj(request, posts),
    }
    return render(request, "posts/index.html", context)


def group_posts(request, slug):
    """
    Страница сообщества. Возвращает последние 10 постов сообщества.
    """
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.select_related("author")
    context = {
        "group": group,
        "page_obj": get_page_obj(request, posts),
    }
    return render(request, "posts/group_list.html", context)


def profile(request, username):
    """
    Страница профиля пользователя со всеми постами пользователя.
    """
    author = get_object_or_404(User, username=username)
    posts = author.posts.select_related("group")
    posts_count = posts.count()

    following = request.user.is_authenticated and Follow.objects.filter(
        user=request.user, author=author
    )

    context = {
        'author': author,
        'page_obj': get_page_obj(request, posts),
        'posts_count': posts_count,
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    """
    Страница поста. Возвращает текст поста, имя автора, дату публикации,
    имя группы с ссылкой на все записи группы, ссылку на все записи автора и
    общее количество постов автора.
    """
    post = get_object_or_404(Post, pk=post_id)
    posts_count: str = Post.objects.filter(author=post.author).count()
    comments = post.comments.select_related("author", "post")
    form = CommentForm()

    context = {
        "post": post,
        'posts_count': posts_count,
        'comments': comments,
        'form': form,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    """
    Страница создания нового поста.
    """
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', request.user)
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    """
    Страница редактирования поста.
    """
    forum_post = get_object_or_404(Post, pk=post_id)
    form = PostForm(
        request.POST or None, files=request.FILES or None, instance=forum_post
    )
    if forum_post.author != request.user:
        return redirect('posts:post_detail', post_id)
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', forum_post.pk)
    context = {
        'form': form,
        'is_edit': True,
        'post': forum_post,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    """
    Функция для добавления комментария к посту.
    """
    form = CommentForm(request.POST or None)
    post = get_object_or_404(Post, pk=post_id)

    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    """
    Страница с постами, на которые подписан текущий пользователь,
    отсоритированая по дате добавления поста.
    """

    posts = Post.objects.filter(author__following__user=request.user)

    context = {'page_obj': get_page_obj(request, posts)}
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    """
    Добавление подписок на авторов. Автор не может подписаться сам на себя.
    А жаль, хорошего человека приятно иметь в ленте подписок.
    """
    author = get_object_or_404(User, username=username)
    user = get_object_or_404(User, username=request.user)

    if (
        author != request.user
        and not Follow.objects.filter(user=user, author=author).exists()
    ):
        Follow.objects.create(user=user, author=author)

    return redirect('posts:follow_index')


@login_required
def profile_unfollow(request, username):
    """
    Функция удаления автора из подписок.
    """
    author = get_object_or_404(User, username=username)

    if Follow.objects.filter(user=request.user, author=author).exists():
        Follow.objects.get(user=request.user, author=author).delete()

    return redirect('posts:follow_index')

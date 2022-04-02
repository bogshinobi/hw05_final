from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import PostForm, CommentForm
from .models import Follow, Group, Post, Comment, User
from .utils import page_context


def index(request):
    context = page_context(request, Post.objects.all())
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    context = page_context(request, group.posts.all())
    context.update(group=group)
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    user = get_object_or_404(User, username=username)
    context = page_context(request, user.posts.all())
    following = Follow.objects.filter(user=request.user, author=user).exists()
    context.update(author=user, following=following)
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    comments = Comment.objects.filter(post=post)
    context = {
        'post': post,
        'form': form,
        'comments': comments
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        form = form.save(commit=False)
        form.author = request.user
        form.save()
        return redirect('posts:profile', request.user)
    context = {
        'form': form,
    }
    return render(request, 'posts/post_create.html', context)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post.id)
    form = PostForm(
        request.POST or None, files=request.FILES or None, instance=post
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post.id)
    context = {
        'form': form,
        'post_id': post.id,
        'is_edit': True
    }
    return render(request, 'posts/post_create.html', context)

@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)

@login_required
def follow_index(request):
    context = page_context(
        request, Post.objects.filter(author__following__user=request.user)
    )
    return render(request, 'posts/follow.html', context)

@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user != author:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('posts:profile', author)

@login_required
def profile_unfollow(request, username):
    Follow.objects.filter(
        user=request.user, author__username=username
    ).delete()
    return redirect('posts:profile', username)
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User


@require_GET
def index(request):
    posts = Post.objects.all()
    paginator = Paginator(posts, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    return render(
        request, "posts/index.html", {"page": page, "paginator": paginator}
    )


@require_GET
def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    paginator = Paginator(posts, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    return render(
        request,
        "posts/group.html",
        {"group": group, "page": page, "paginator": paginator},
    )


@require_GET
def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = author.posts.all()
    paginator = Paginator(posts, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    follow = False
    if request.user.is_authenticated:
        follow = Follow.objects.filter(
            author=author, user=request.user
        ).exists()
    return render(
        request,
        "posts/profile.html",
        {
            "author": author,
            "page": page,
            "paginator": paginator,
            "follow": follow,
        },
    )


@require_GET
def post_view(request, username, post_id):
    author = get_object_or_404(User, username=username)
    post = get_object_or_404(Post, pk=post_id, author=author)
    comments = post.comments.all()
    form = CommentForm()
    return render(
        request,
        "posts/post.html",
        {"author": author, "post": post, "comments": comments, "form": form},
    )


@login_required
@require_http_methods(["GET", "POST"])
def new_post(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect("posts:index")
    return render(request, "posts/new_post.html", {"form": form})


@login_required
@require_http_methods(["GET", "POST"])
def post_edit(request, username, post_id):
    post = get_object_or_404(Post, pk=post_id, author__username=username)
    if post.author != request.user:
        return redirect("posts:post", username, post_id)
    form = PostForm(
        request.POST or None, files=request.FILES or None, instance=post
    )
    if form.is_valid():
        post.save()
        return redirect("posts:post", username, post_id)
    return render(
        request,
        "posts/new_post.html",
        {"form": form, "username": username, "post_id": post_id, "post": post},
    )


@login_required
@require_http_methods(["GET", "POST"])
def add_comment(request, username, post_id):
    author = get_object_or_404(User, username=username)
    post = get_object_or_404(Post, pk=post_id)
    comments = post.comments.all()
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
        return redirect("posts:post", username, post_id)
    return render(
        request,
        "posts/post.html",
        {"author": author, "comments": comments, "post": post, "form": form},
    )


@login_required
def follow_index(request):
    posts = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(posts, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    return render(
        request, "posts/follow.html", {"page": page, "paginator": paginator}
    )


@login_required
def profile_follow(request, username):
    user = get_object_or_404(User, username=request.user)
    author = get_object_or_404(User, username=username)
    if user != author:
        Follow.objects.get_or_create(user=user, author=author)
    return redirect("posts:profile", username)


@login_required
def profile_unfollow(request, username):
    unfollow_from_author = get_object_or_404(User, username=username)
    Follow.objects.filter(
        user=request.user, author=unfollow_from_author
    ).delete()
    return redirect("posts:profile", username)

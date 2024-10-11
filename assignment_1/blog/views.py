from django.shortcuts import render, get_object_or_404
from .models import Post, Comment
from django.shortcuts import redirect
from django.http import HttpResponseForbidden
from .forms import PostForm, CommentForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.contrib import messages
from django.views.decorators.cache import cache_page
from django.core.cache import cache


def get_comment_count(post_id):
    cache_key = f'comment_count_{post_id}'
    comment_count = cache.get(cache_key)

    if comment_count is None:
        comment_count = Comment.objects.filter(post_id=post_id).count()
        cache.set(cache_key, comment_count, timeout=60)

    return comment_count


# @cache_page(60 * 1)
def post_list(request):
    posts = Post.objects.all().order_by('-created_at')
    paginator = Paginator(posts, 5)  # Show 5 posts per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'blog/post_list.html', {'page_obj': page_obj})

def post_detail(request, post_id):
    cache_key = f'post_detail_{post_id}'
    post = cache.get(cache_key)

    if post is None:
        post = get_object_or_404(Post, id=post_id)
        cache.set(cache_key, post, timeout=60)  

    comments_cache_key = f'post_comments_{post_id}'
    comments = cache.get(comments_cache_key)

    if comments is None:
        comments = post.comments.all()
        cache.set(comments_cache_key, comments, timeout=60)  

    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()

            cache.delete(comments_cache_key)

            return redirect('post_detail', post_id=post.id)
    else:
        form = CommentForm()

    return render(request, 'blog/post_detail.html', {'post': post, 'comments': comments, 'form': form})


@login_required
def post_create(request):
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user 
            post.save()
            return redirect('post_list')
    else:
        form = PostForm()
    return render(request, 'blog/post_form.html', {'form': form})

@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.user != post.author:
        return redirect('post_list')
    if request.method == 'POST':
        form = PostForm(request.POST, instance=post)
        if form.is_valid():
            form.save()
            return redirect('post_detail', post_id=post.id)
    else:
        form = PostForm(instance=post)
    return render(request, 'blog/post_form.html', {'form': form})

@login_required
def post_delete(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.user != post.author:
        return HttpResponseForbidden()
    if request.method == 'POST':
        post.delete()
        return redirect('post_list')
    return render(request, 'blog/post_confirm_delete.html', {'post': post})




def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! You can now log in.')
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'blog/register.html', {'form': form})
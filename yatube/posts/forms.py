from django import forms

from .models import Comment, Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ["text", "group", "image"]
        labels = {
            "text": "Текст поста",
            "group": "Выберите группу",
            "image": "Добавьте картинку",
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["text"]

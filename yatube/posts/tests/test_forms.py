import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from posts.forms import PostForm
from posts.models import Group, Post

User = get_user_model()


class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        cls.user = User.objects.create(username="Dmitriy")
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="test_group",
            description="Тестовая группа для теста",
        )
        cls.another_group = Group.objects.create(
            title="Вторая группа",
            slug="another_group",
            description="Вторая группа для теста",
        )
        cls.post = Post.objects.create(
            text="Тестовый текст of Posts",
            author=PostCreateFormTests.user,
            group=PostCreateFormTests.group,
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Проверка создания нового поста c указанием группы"""
        posts_count = Post.objects.count()
        small_gif = (
            b"\x47\x49\x46\x38\x39\x61\x01\x00"
            b"\x01\x00\x00\x00\x00\x21\xf9\x04"
            b"\x01\x0a\x00\x01\x00\x2c\x00\x00"
            b"\x00\x00\x01\x00\x01\x00\x00\x02"
            b"\x02\x4c\x01\x00\x3b"
        )
        uploaded = SimpleUploadedFile(
            name="small.gif", content=small_gif, content_type="image/gif"
        )
        form_data = {
            "text": "Тестовый текст",
            "group": PostCreateFormTests.group.id,
            "image": uploaded,
        }
        response = self.authorized_client.post(
            reverse("posts:new_post"), data=form_data, follow=True
        )
        self.assertRedirects(response, reverse("posts:index"))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text="Тестовый текст",
                author=PostCreateFormTests.user,
                group=PostCreateFormTests.group,
                image="posts/small.gif",
            ).exists()
        )

    def test_create_post_without_group(self):
        """Проверка создания нового поста без группы"""
        posts_count = Post.objects.count()
        form_data = {
            "text": "Тестовый текст",
        }
        response = self.authorized_client.post(
            reverse("posts:new_post"), data=form_data, follow=True
        )
        self.assertRedirects(response, reverse("posts:index"))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text="Тестовый текст",
                author=PostCreateFormTests.user,
                group__isnull=True,
            ).exists()
        )

    def test_post_edit(self):
        """Проверка редактирования поста и группы"""
        post = self.post
        form_data = {
            "text": "Изменённый Тестовый текст",
            "group": self.another_group.id,
        }
        response = self.authorized_client.post(
            reverse(
                "posts:post_edit",
                kwargs={"username": self.user.username, "post_id": post.id},
            ),
            data=form_data,
            follow=True,
        )
        post.refresh_from_db()
        self.assertEqual(post.text, "Изменённый Тестовый текст")
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.group, self.another_group)
        self.assertRedirects(response, "/Dmitriy/1/")

    def test_post_edit_only_text(self):
        """Проверка редактирования текста поста без группы"""
        post = self.post
        form_data = {
            "text": "Изменённый Тестовый текст без группы",
        }
        response = self.authorized_client.post(
            reverse(
                "posts:post_edit",
                kwargs={
                    "username": self.user.username,
                    "post_id": self.post.id,
                },
            ),
            data=form_data,
            follow=True,
        )
        post.refresh_from_db()
        self.assertEqual(post.text, "Изменённый Тестовый текст без группы")
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.group, None)
        self.assertRedirects(response, "/Dmitriy/1/")

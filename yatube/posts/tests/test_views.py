import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.forms import PostForm
from posts.models import Comment, Follow, Group, Post

User = get_user_model()


@override_settings(MEDIA_ROOT=tempfile.mkdtemp(dir=settings.BASE_DIR))
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username="Dmitriy")
        cls.another_user = User.objects.create(username="Follower")
        cls.group = Group.objects.create(
            title="Dmitriy_Notes", slug="DK", description="Записи Дмитрия"
        )
        cls.another_group = Group.objects.create(
            title="Second_G", slug="2G", description="Вторая группа"
        )
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
        cls.post = Post.objects.create(
            text="Тестовый текст of Posts",
            pub_date="19.07.2021",
            author=PostPagesTests.user,
            group=PostPagesTests.group,
            image=uploaded,
        )
        cls.comment = Comment.objects.create(
            post=cls.post, author=cls.user, text="comment_text"
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.another_auth_client = Client()
        self.another_auth_client.force_login(self.another_user)
        cache.clear()

    def test_pages_use_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            "posts/index.html": reverse("posts:index"),
            "posts/group.html": reverse("posts:group", kwargs={"slug": "DK"}),
            "posts/new_post.html": reverse("posts:new_post"),
        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_new_post_page_shows_correct_context(self):
        """Шаблон new_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse("posts:new_post"))
        form_fields = {
            "text": forms.fields.CharField,
            "group": forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context["form"].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_group_posts_detail_pages_show_correct_context(self):
        """Шаблон group сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse("posts:group", kwargs={"slug": "DK"})
        )
        group = response.context["group"]
        first_object = response.context["page"][0]
        self.assertEqual(group.title, "Dmitriy_Notes")
        self.assertEqual(group.description, "Записи Дмитрия")
        self.assertEqual(group.slug, "DK")
        self.assertEqual(first_object.text, PostPagesTests.post.text)
        self.assertEqual(first_object.pub_date, PostPagesTests.post.pub_date)
        self.assertEqual(first_object.author, PostPagesTests.post.author)
        self.assertEqual(first_object.group.title, PostPagesTests.group.title)
        self.assertEqual(first_object.image, PostPagesTests.post.image)

    def test_index_page_shows_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.guest_client.get(reverse("posts:index"))
        first_object = response.context["page"][0]
        self.assertEqual(first_object.text, PostPagesTests.post.text)
        self.assertEqual(first_object.pub_date, PostPagesTests.post.pub_date)
        self.assertEqual(first_object.author, PostPagesTests.post.author)
        self.assertEqual(first_object.group.title, PostPagesTests.group.title)
        self.assertEqual(first_object.image, PostPagesTests.post.image)

    def test_profile_page_shows_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse("posts:profile", kwargs={"username": "Dmitriy"})
        )
        first_object = response.context["page"][0]
        self.assertEqual(first_object.text, PostPagesTests.post.text)
        self.assertEqual(first_object.image, PostPagesTests.post.image)
        self.assertEqual(
            response.context["author"], PostPagesTests.post.author
        )

    def test_post_edit_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(
                "posts:post_edit", kwargs={"username": "Dmitriy", "post_id": 1}
            )
        )
        self.assertIsInstance(response.context["form"], PostForm)

    def test_post_and_comment_shows_correct_context(self):
        """Шаблон post сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(
                "posts:post", args=[self.post.author.username, self.post.id]
            )
        )
        first_object = response.context["post"]
        comment = response.context["comments"][0]
        self.assertEqual(comment.post, PostPagesTests.comment.post)
        self.assertEqual(comment.author, PostPagesTests.comment.author)
        self.assertEqual(comment.text, PostPagesTests.comment.text)
        self.assertEqual(comment.created, PostPagesTests.comment.created)
        self.assertEqual(first_object.text, PostPagesTests.post.text)
        self.assertEqual(first_object.image, PostPagesTests.post.image)
        self.assertEqual(
            response.context["author"], PostPagesTests.post.author
        )

    def test_post_in_group(self):
        """Проверить пост в группах и на главной странице"""
        response = self.guest_client.get(reverse("posts:index"))
        first_object = response.context["page"][0]
        response_in_group = self.guest_client.get(
            reverse("posts:group", kwargs={"slug": "DK"})
        )
        first_object_in_group = response_in_group.context["page"][0]
        self.assertEqual(first_object.text, "Тестовый текст of Posts")
        self.assertEqual(first_object_in_group.text, "Тестовый текст of Posts")
        self.assertEqual(first_object_in_group.group.title, "Dmitriy_Notes")

    def test_post_not_in_another_group(self):
        """Проверить что пост не появился в ненужной группе"""
        response_in_sec_grp = self.guest_client.get(
            reverse("posts:group", kwargs={"slug": "2G"})
        )
        self.assertEqual(response_in_sec_grp.context["page"].has_next(), False)

    def test_create_post_no_authorized_client(self):
        """Проверка не возможности создания нового поста для не авторизованного
        пользовтеля и редиректа на страницу login"""
        posts_count = Post.objects.count()
        form_data = {
            "text": "Тестовый текст",
            "group": PostPagesTests.group.id,
        }
        response = self.guest_client.post(
            reverse("posts:new_post"), data=form_data, follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertRedirects(response, "/auth/login/?next=/new/")

    def test_add_comments_authorized_client(self):
        """Авторизированный пользователь может добавлять комментарии"""
        comments_count = Comment.objects.count()
        form_data = {"text": "текс_комментария"}
        response = self.authorized_client.post(
            reverse(
                "posts:add_comment",
                kwargs={
                    "username": self.user.username,
                    "post_id": self.post.id,
                },
            ),
            data=form_data,
            follow=True,
        )
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertRedirects(response, "/Dmitriy/1/")
        Comment.objects.filter(
            text="текс_комментария", author=self.user, post=self.post
        ).exists()

    def test_add_comments_no_authorized_client(self):
        """Невторизированный пользователь не может добавлять комментарии"""
        comments_count = Comment.objects.count()
        form_data = {"text": "коммент"}
        response = self.guest_client.post(
            reverse(
                "posts:add_comment",
                kwargs={
                    "username": self.user.username,
                    "post_id": self.post.id,
                },
            ),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(response, "/auth/login/?next=/Dmitriy/1/comment")
        self.assertEqual(Comment.objects.count(), comments_count)

    def test_follow_authorized_client(self):
        """Авторизованный пользователь может подписываться на юзера"""
        followings_count = Follow.objects.count()
        self.authorized_client.post(
            reverse(
                "posts:profile_follow",
                kwargs={"username": self.another_user.username},
            ),
            follow=True,
        )
        follow = Follow.objects.first()
        self.assertEqual(Follow.objects.count(), followings_count + 1)
        self.assertEqual(follow.author, self.another_user)
        self.assertEqual(follow.user, self.user)

    def test_unfollow_authorized_client(self):
        """Авторзиованный пользователь может отписываться от юзера"""
        Follow.objects.create(
            user=self.user,
            author=self.another_user,
        )
        self.assertEqual(Follow.objects.count(), 1)
        self.authorized_client.post(
            reverse(
                "posts:profile_unfollow",
                kwargs={"username": self.another_user.username},
            ),
            follow=True,
        )
        self.assertEqual(Follow.objects.count(), 0)

    def test_new_post_on_page_followers(self):
        """Новая запись пользователя появляется в ленте подписчиков"""
        Follow.objects.create(
            user=self.another_user,
            author=self.user,
        )
        response = self.another_auth_client.get(reverse("posts:follow_index"))
        first_object = response.context["page"][0]
        self.assertEqual(first_object, self.post)

    def test_new_post_not_on_page_non_followers(self):
        """Новая запись пользователя не появляется в ленте не подписчиков"""
        not_follower = User.objects.create_user(username="notfollower")
        authorized_not_follower = Client()
        authorized_not_follower.force_login(not_follower)
        response = authorized_not_follower.get(reverse("posts:follow_index"))
        posts = response.context["page"]
        self.assertEqual(len(posts), 0)

    def test_cache(self):
        """Тест кэширования главной страницы"""
        response = self.authorized_client.get(reverse("posts:index"))
        content = response.content
        Post.objects.all().delete()
        response = self.authorized_client.get(reverse("posts:index"))
        self.assertEqual(content, response.content)
        cache.clear()
        response = self.authorized_client.get(reverse("posts:index"))
        self.assertNotEqual(content, response.content)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="Dmitriy")
        cls.group = Group.objects.create(
            title="Dmitriy_Notes", slug="DK", description="Записи Дмитрия"
        )
        Post.objects.bulk_create(
            (
                Post(text="text %s" % i, author=cls.user, group=cls.group)
                for i in range(13)
            )
        )

    def setUp(self):
        self.guest_client = Client()

    def test_first_page_contains_ten_records(self):
        """Проверка паджинатора: 10 записей на 1 странице"""
        pages_names = (
            reverse("posts:index"),
            reverse("posts:group", kwargs={"slug": "DK"}),
            reverse("posts:profile", kwargs={"username": "Dmitriy"}),
        )
        for adress in pages_names:
            response = self.guest_client.get(adress)
            self.assertEqual(len(response.context["page"].object_list), 10)

    def test_second_page_contains_three_records(self):
        """Проверка паджинатора: 3 записи на 2 странице"""
        pages_names = (
            reverse("posts:index"),
            reverse("posts:group", kwargs={"slug": "DK"}),
            reverse("posts:profile", kwargs={"username": "Dmitriy"}),
        )
        for adress in pages_names:
            response = self.guest_client.get(adress + "?page=2")
            self.assertEqual(len(response.context["page"].object_list), 3)

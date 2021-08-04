from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post

User = get_user_model()


class PostUrlTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="DmitriK")
        cls.not_author = User.objects.create(username="not_author")
        cls.group = Group.objects.create(
            title="Dmitriy_Notes", slug="DK", description="Записи Дмитрия"
        )
        cls.post = Post.objects.create(
            text="Тестовый текст of Posts", author=cls.user, group=cls.group
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.not_author_client = Client()
        self.authorized_client.force_login(PostUrlTests.user)
        self.not_author_client.force_login(PostUrlTests.not_author)

    def test_posts_url_exists_at_desired_location_non_authorized(self):
        """Проверка доступности страниц не авторизованному пользователю."""
        pages_names = (
            reverse("posts:index"),
            reverse("posts:group", kwargs={"slug": "DK"}),
            reverse("posts:profile", kwargs={"username": "DmitriK"}),
            reverse(
                "posts:post", kwargs={"username": "DmitriK", "post_id": 1}
            ),
            reverse("about:author"),
            reverse("about:tech"),
        )
        for adress in pages_names:
            response = self.guest_client.get(adress)
            self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_posts_url_exists_at_desired_location_authorized(self):
        """Проверка доступности страниц авторизованному пользователю."""
        pages_names = (
            reverse("posts:index"),
            reverse("posts:group", kwargs={"slug": "DK"}),
            reverse("posts:new_post"),
            reverse(
                "posts:post_edit", kwargs={"username": "DmitriK", "post_id": 1}
            ),
        )
        for adress in pages_names:
            response = self.authorized_client.get(adress)
            self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_new_post_url_redirect_anonymous_on_admin_login(self):
        """
        Страница по адресу /new/ перенаправит анонимного
        пользователя на страницу логина.
        """
        response = self.guest_client.get("/new/", follow=True)
        self.assertRedirects(response, "/auth/login/?next=/new/")

    def test_post_edit_url_redirect_anonymous_on_admin_login(self):
        """
        Страница по адресу /username/post_id/edit перенаправит анонимного
        пользователя на страницу логина.
        """
        response = self.guest_client.get(
            (
                reverse(
                    "posts:post_edit",
                    kwargs={"username": "DmitriK", "post_id": 1},
                )
            ),
            follow=True,
        )
        self.assertRedirects(response, "/auth/login/?next=/DmitriK/1/edit/")

    def test_post_edit_url_redirect_non_author_on_post_page(self):
        """
        Страница по адресу /username/post_id/edit перенаправит не автора
        на страницу поста.
        """
        response = self.not_author_client.get(
            (
                reverse(
                    "posts:post_edit",
                    kwargs={"username": "DmitriK", "post_id": 1},
                )
            ),
            follow=True,
        )
        self.assertRedirects(response, "/DmitriK/1/")

    def test_posts_pages_use_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            "/": "posts/index.html",
            "/group/DK/": "posts/group.html",
            "/new/": "posts/new_post.html",
            "/DmitriK/1/edit/": "posts/new_post.html",
        }
        for url, template in templates_pages_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_not_existing_url_code_404(self):
        """Если страница не найдена, сервер возвращает код 404"""
        response = self.guest_client.get("/wrong_page/")
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

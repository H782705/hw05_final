from http import HTTPStatus

from django.test import Client, TestCase


class StaticURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_posts_url_exists_at_desired_location_non_authorized(self):
        """Проверка доступности страниц не авторизованному пользователю."""
        pages_names = (
            "/about/author/",
            "/about/tech/",
        )
        for adress in pages_names:
            response = self.guest_client.get(adress)
            self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_about_pages_use_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            "/about/author/": "about/author.html",
            "/about/tech/": "about/tech.html",
        }
        for url, template in templates_pages_names.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertTemplateUsed(response, template)

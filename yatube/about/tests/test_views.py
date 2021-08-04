from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse


class StaticViewsTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_about_pages_accessible_by_name(self):
        """
        URL, генерируемые при помощи имени about:authot and tech, доступны.
        """
        pages_names = (
            reverse("about:author"),
            reverse("about:tech"),
        )
        for adress in pages_names:
            response = self.guest_client.get(adress)
            self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_about_pages_use_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse("about:author"): "about/author.html",
            reverse("about:tech"): "about/tech.html",
        }
        for url, template in templates_pages_names.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertTemplateUsed(response, template)

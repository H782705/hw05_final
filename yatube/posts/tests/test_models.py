from django.contrib.auth import get_user_model
from django.test import TestCase

from posts.models import Group, Post

User = get_user_model()


class PostModelTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="Dmitriy")
        cls.post = Post.objects.create(
            text="Тестовый текст of Posts",
            author=cls.user,
        )

    def test_str_post(self):
        test_text = PostModelTests.post
        expected_object_name = test_text.text[:15]
        self.assertEqual(expected_object_name, str(test_text))


class GroupModelTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title="Dmitriy_Notes", slug="DK", description="Записи Дмитрия"
        )

    def test_str_group(self):
        test_group = GroupModelTests.group
        expected_group_name = test_group.title
        self.assertEqual(expected_group_name, str(test_group))

from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from posts.models import Group, Post

User = get_user_model()


class URLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создадим запись в БД для проверки адресов
        cls.author = User.objects.create_user(
            username='abcUser',
        )
        cls.author2 = User.objects.create_user(
            username='abcUser2',
        )
        cls.group = Group.objects.create(
            title="Тестовый заголовок",
            slug="test-slug",
        )
        cls.new_post = Post.objects.create(
            text='Тестовый текст', author=cls.author, group=cls.group
        )

        cls.URL_ADDRESSES_WITH_TEMPLATES: tuple = (
            ('/', 'posts/index.html'),
            (f'/group/{cls.group.slug}/', 'posts/group_list.html'),
            (f'/profile/{cls.author.username}/', 'posts/profile.html'),
            (f'/posts/{cls.new_post.pk}/', 'posts/post_detail.html'),
        )

        cls.AUTH_ADDRESSES_WITH_TEMPLATES: tuple = (
            ('/create/', 'posts/create_post.html'),
            (f'/posts/{cls.new_post.pk}/edit/', 'posts/create_post.html'),
        )

    def setUp(self):
        # неавторизированный клиент
        self.guest_client = Client()

        # авторизированный клиент
        self.authorized_client = Client()
        self.authorized_client.force_login(URLTests.author)

        # авторизированный клиент_2
        self.authorized_client2 = Client()
        self.authorized_client2.force_login(URLTests.author2)

    def test_urls_guest_availability(self):
        """
        Проверка доступности адресов для неавторизированных пользователей.
        """
        # Проверка работы общедоступных адресов
        for address, template in self.URL_ADDRESSES_WITH_TEMPLATES:
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

        # Доступ гостей к страницам для зарегистрированных пользователей
        for address, template in self.AUTH_ADDRESSES_WITH_TEMPLATES:
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertRedirects(response, f'/auth/login/?next={address}')

    def test_urls_auth_availability(self):
        """
        Проверка доступности адресов для авторизированных пользователей.
        """
        # Проверка работы адресов для авторизированных пользователей
        for address, template in self.AUTH_ADDRESSES_WITH_TEMPLATES:
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

        # Проверка возможности редактирования чужого поста
        edit_page = self.authorized_client2.get(
            f'/posts/{URLTests.new_post.pk}/edit/'
        )
        self.assertEqual(edit_page.status_code, HTTPStatus.FOUND)

    def test_404_page(self):
        """
        Проверка доступности несуществующей страницы.
        """
        broken_page = self.guest_client.get('broken_page/')
        self.assertEqual(broken_page.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_and_templates_validataion(self):
        """
        Проверка соответствия вызываемого адреса и html темплейта.
        """

        for address, template in self.URL_ADDRESSES_WITH_TEMPLATES:
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

        for address, template in self.AUTH_ADDRESSES_WITH_TEMPLATES:
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

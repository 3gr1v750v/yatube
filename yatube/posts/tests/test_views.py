import shutil
import tempfile
from http import HTTPStatus

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.models import Comment, Follow, Group, Post

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class DataBaseRecords(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.author = User.objects.create_user(
            username='abcUser',
        )
        cls.follower = User.objects.create_user(
            username='followerUser',
        )

        number_of_groups: int = 2

        for group in range(number_of_groups):
            Group.objects.create(
                title=f"Группа номер {group}",
                slug=f"test-slug{group}",
                description=f"Описание группы номер {group}",
            )

        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif', content=small_gif, content_type='image/gif'
        )

        cls.number_of_records: int = 12

        # 12 постов, где первый принадлежит другой группе
        for record in range(cls.number_of_records):
            if record == 1:
                Post.objects.create(
                    text=f'Пост номер {record}',
                    author=cls.author,
                    group=Group.objects.first(),
                    image=uploaded,
                )
            Post.objects.create(
                text=f'Пост номер {record}',
                author=cls.author,
                group=Group.objects.last(),
                image=uploaded,
            )

        # 12 комментов, где первый принадлежит другому посту
        for record in range(cls.number_of_records):
            if record == 1:
                Comment.objects.create(
                    text=f'Комментарий номер {record}',
                    author=cls.author,
                    post=Post.objects.first(),
                )
            Comment.objects.create(
                text=f'Комментарий номер {record}',
                author=cls.author,
                post=Post.objects.last(),
            )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        cache.clear()
        # неавторизированный клиент
        self.guest_client = Client()

        # авторизированный клиент
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

        self.follower_client = Client()
        self.follower_client.force_login(self.follower)

        self.index_response = self.authorized_client.get(
            reverse('posts:index')
        )
        self.group_response = self.authorized_client.get(
            reverse(
                'posts:group_list', kwargs={'slug': Group.objects.last().slug}
            )
        )
        self.profile_response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.author.username})
        )
        self.post_detail = self.authorized_client.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': Post.objects.first().pk},
            )
        )
        self.post_detail_comments = self.authorized_client.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': Post.objects.last().pk},
            )
        )
        self.post_create = self.authorized_client.get(
            reverse('posts:post_create')
        )
        self.post_edit = self.authorized_client.get(
            reverse(
                'posts:post_edit', kwargs={'post_id': Post.objects.first().pk}
            )
        )
        self.comment_create = self.authorized_client.get(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': Post.objects.first().pk},
            )
        )


class TemplateTests(DataBaseRecords):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.TEMPLATE_PAGE_NAMES: tuple = (
            (reverse('posts:index'), 'posts/index.html'),
            (
                reverse(
                    'posts:group_list',
                    kwargs={'slug': Group.objects.last().slug},
                ),
                'posts/group_list.html',
            ),
            (
                reverse(
                    'posts:profile', kwargs={'username': cls.author.username}
                ),
                'posts/profile.html',
            ),
            (
                reverse(
                    'posts:post_detail',
                    kwargs={'post_id': Post.objects.first().pk},
                ),
                'posts/post_detail.html',
            ),
            (reverse('posts:post_create'), 'posts/create_post.html'),
            (
                reverse(
                    'posts:post_edit',
                    kwargs={'post_id': Post.objects.first().pk},
                ),
                'posts/create_post.html',
            ),
            (reverse('about:author'), 'about/author.html'),
            (reverse('about:tech'), 'about/tech.html'),
        )

    def test_pages_uses_correct_template(self):
        cache.clear()
        """Проверка, что View-функция использует соответствующий шаблон."""
        for reverse_name, template in self.TEMPLATE_PAGE_NAMES:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)


class ContextTests(DataBaseRecords):
    def test_index_page_show_correct_context(self):

        reference_post = Post.objects.latest('pub_date')

        # Содержимое первого элемента на совпадает с ожидаеним на странице
        first_object = self.index_response.context['page_obj'][0]
        self.assertEqual(first_object.text, reference_post.text)
        self.assertEqual(
            first_object.author.username, reference_post.author.username
        )
        self.assertEqual(first_object.group.title, reference_post.group.title)
        self.assertEqual(first_object.image, reference_post.image)

    def test_group_posts_show_correct_context(self):

        reference_post = Post.objects.filter(
            group=Group.objects.last().pk
        ).latest('pub_date')

        # Содержимое первого элемента совпадает с ожидаеним
        first_object = self.group_response.context['page_obj'][0]
        self.assertEqual(first_object.text, reference_post.text)
        self.assertEqual(
            first_object.author.username, reference_post.author.username
        )
        self.assertEqual(first_object.group.title, reference_post.group.title)
        self.assertEqual(first_object.group.slug, reference_post.group.slug)
        self.assertEqual(first_object.image, reference_post.image)

    def test_profile_shows_correct_context(self):

        reference_post = Post.objects.latest('pub_date')

        first_object = self.profile_response.context['page_obj'][0]

        self.assertEqual(first_object.text, reference_post.text)
        self.assertEqual(
            first_object.author.username, reference_post.author.username
        )
        self.assertEqual(first_object.group.title, reference_post.group.title)
        self.assertEqual(first_object.group.slug, reference_post.group.slug)
        self.assertEqual(first_object.image, reference_post.image)

    def test_post_detail_show_correct_context(self):
        reference_post = Post.objects.first()

        self.assertEqual(
            self.post_detail.context.get('post').text, reference_post.text
        )
        self.assertEqual(
            self.post_detail.context.get('post').author.username,
            reference_post.author.username,
        )
        self.assertEqual(
            self.post_detail.context.get('post').group.title,
            reference_post.group.title,
        )
        self.assertEqual(
            self.post_detail.context.get('post').group.slug,
            reference_post.group.slug,
        )
        self.assertEqual(
            self.post_detail.context.get('post').image, reference_post.image
        )


class PaginatorTests(DataBaseRecords):
    def test_index_page_paginator(self):

        self.assertEqual(
            len(self.index_response.context['page_obj']),
            settings.RECORDS_PER_PAGE,
        )

        response_page_2 = self.authorized_client.get(
            reverse('posts:index') + '?page=2'
        )
        self.assertEqual(
            len(response_page_2.context['page_obj']),
            Post.objects.count() - settings.RECORDS_PER_PAGE,
        )

    def test_profile_paginator(self):

        self.assertEqual(
            len(self.profile_response.context['page_obj']),
            settings.RECORDS_PER_PAGE,
        )

        response_page_2 = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.author.username})
            + '?page=2'
        )
        self.assertEqual(
            len(response_page_2.context['page_obj']),
            Post.objects.count() - settings.RECORDS_PER_PAGE,
        )

    def test_group_page_paginator(self):

        self.assertEqual(
            len(self.group_response.context['page_obj']),
            settings.RECORDS_PER_PAGE,
        )

        # Группа должна содержать 11 постов. 12 пост принадлежит другой группе
        response_page_2 = self.authorized_client.get(
            reverse(
                'posts:group_list', kwargs={'slug': Group.objects.last().slug}
            )
            + '?page=2'
        )
        self.assertEqual(
            len(response_page_2.context['page_obj']),
            self.number_of_records - settings.RECORDS_PER_PAGE,
        )


class PostFieldTypesTests(DataBaseRecords):
    def test_post_create_show_correct_field_types(self):
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }

        # Типы полей формы в словаре context соответствуют ожиданиям
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = self.post_create.context.get('form').fields.get(
                    value
                )
                self.assertIsInstance(form_field, expected)

    def test_post_edit_shows_correct_field_types(self):
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }

        # Типы полей формы в словаре context соответствуют ожиданиям
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = self.post_edit.context.get('form').fields.get(
                    value
                )
                self.assertIsInstance(form_field, expected)


class CommentTests(DataBaseRecords):
    def test_post_page_show_correct_comments_context(self):

        reference_comment = Comment.objects.filter(
            post=Post.objects.last().pk
        ).latest('created')

        # Содержимое первого элемента совпадает с ожидаеним на странице
        first_object = self.post_detail_comments.context['comments'][0]

        self.assertEqual(first_object.text, reference_comment.text)
        self.assertEqual(
            first_object.author.username, reference_comment.author.username
        )


class CommentFieldTypesTests(DataBaseRecords):
    def test_comment_create_show_correct_field_types(self):
        form_fields = {
            'text': forms.fields.CharField,
        }

        # Типы полей формы в словаре context соответствуют ожиданиям
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = self.post_detail_comments.context.get(
                    'form'
                ).fields.get(value)
                self.assertIsInstance(form_field, expected)


class IndexPageCacheTest(DataBaseRecords):
    def test_index_page_cache(self):

        response_1 = self.guest_client.get(reverse("posts:index"))

        Post.objects.all().delete

        response_2 = self.guest_client.get(reverse("posts:index"))
        self.assertEqual(response_1.content, response_2.content)

        cache.clear()

        response_3 = self.guest_client.get(reverse("posts:index"))
        self.assertNotEqual(response_1.content, response_3.content)


class PostFollowTests(DataBaseRecords):
    def test_follow_and_unfollow(self):
        """
        Авторизованный пользователь может подписываться на других
        пользователей и удалять их из подписок.
        """
        # создание подписки
        self.follower_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.author.username},
            )
        )
        self.assertEqual(Follow.objects.filter(user=self.follower).count(), 1)

        # удаление подписки
        self.follower_client.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': self.author.username},
            )
        )
        self.assertEqual(Follow.objects.filter(user=self.follower).count(), 0)

    def test_follow_index(self):
        """
        Новая запись пользователя появляется в ленте тех, кто на него
        подписан и не появляется в ленте тех, кто не подписан.
        """
        # создание подписки через базу
        Follow.objects.create(user=self.follower, author=self.author)
        response_follower = self.follower_client.get(
            reverse('posts:follow_index')
        )
        self.assertEqual(
            len(response_follower.context['page_obj']),
            settings.RECORDS_PER_PAGE,
        )

        # проверка подписки у другого пользователя
        response_author = self.authorized_client.get(
            reverse('posts:follow_index')
        )
        self.assertEqual(len(response_author.context['page_obj']), 0)

    def test_guest_client_follow(self):
        """
        Проверка возможности подписки для неавторизованного клиента.
        """
        # создание подписки
        response = self.guest_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.author.username},
            )
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

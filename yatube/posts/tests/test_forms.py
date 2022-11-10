import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.models import Comment, Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class DataBaseRecords(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создаем запись в базе данных
        cls.author = User.objects.create_user(
            username='abcUser',
        )
        cls.group = Group.objects.create(
            title="Тестовый заголовок",
            slug="test-slug",
        )
        cls.new_post = Post.objects.create(
            text='Тестовый текст',
            author=cls.author,
            group=cls.group,
        )
        cls.comment = Comment.objects.create(
            text="Тестовый комментарий",
            author=cls.author,
            post=cls.new_post,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        # неавторизированный клиент
        self.guest_client = Client()

        # авторизированный клиент
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )

        self.uploaded = SimpleUploadedFile(
            name='small.gif', content=small_gif, content_type='image/gif'
        )


class PostCreateEditTests(DataBaseRecords):
    def test_create_post(self):
        """Валидная форма создает запись в Post."""

        # Считаем количество записей в базе
        tasks_count = Post.objects.count()

        # отправляем новые данные
        form_data = {
            'text': f'{self.new_post.text}-новый',
            'group': self.group.pk,
            'image': self.uploaded,
        }

        response = self.authorized_client.post(
            reverse('posts:post_create'), data=form_data, follow=True
        )

        # Проверка редиректа
        self.assertRedirects(
            response,
            reverse(
                'posts:profile',
                kwargs={'username': self.new_post.author.username},
            ),
        )
        # Проверяем, увеличилось ли число постов
        self.assertEqual(Post.objects.count(), tasks_count + 1)

        # Проверяем, что создалась запись с заданным слагом
        post = Post.objects.latest('pub_date')

        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group.pk, form_data['group'])
        self.assertEqual(post.author, self.author)
        self.assertEqual(
            post.image.name.split('/')[1], form_data['image'].name
        )

        # удаляем загруженную картинку, чтобы следующие тесты не дублировали
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_create_post_by_guest_client(self):
        """
        Проверка возможности создания поста анонимным пользователем.
        """

        tasks_count = Post.objects.count()

        form_data = {
            'text': f'{self.new_post.text}-гость',
            'group': self.group.pk,
        }

        response = self.guest_client.post(
            reverse('posts:post_create'), data=form_data, follow=True
        )

        # Количество записей в базе не изменилось
        self.assertEqual(Post.objects.count(), tasks_count)

        self.assertRedirects(response, '/auth/login/?next=/create/')

    def test_edit_post(self):
        """Валидная форма редактирует запись в Post."""

        tasks_count = Post.objects.count()

        form_data = {
            'text': f'{self.new_post.text}-замена',
            'group': self.group.pk,
            'image': self.uploaded,
        }

        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.new_post.pk}),
            data=form_data,
            follow=True,
        )

        # Проверяем редирект
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': self.new_post.pk}),
        )

        # Проверяем, что произошло редактирование, а не создалась запись.
        self.assertEqual(Post.objects.count(), tasks_count)

        # Проверяем, что изменилась запись с заданным слагом
        post = Post.objects.get(pk=self.new_post.pk)

        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group.pk, form_data['group'])
        self.assertEqual(post.author, self.author)
        self.assertEqual(
            post.image.name.split('/')[1], form_data['image'].name
        )

        # удаляем загруженную картинку, чтобы следующие тесты не дублировали
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)


class CommentCreateTests(DataBaseRecords):
    def test_create_comment(self):
        """Валидная форма создает запись Comment в Post."""

        # Считаем количество записей в базе
        comment_count = Comment.objects.count()

        # отправляем новые данные
        form_data = {
            'text': f'{self.comment.text}-новый',
        }

        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.new_post.pk}),
            data=form_data,
            follow=True,
        )

        # Проверка редиректа
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': self.new_post.pk}),
        )
        # Проверяем, увеличилось ли число постов
        self.assertEqual(Comment.objects.count(), comment_count + 1)

        # Проверяем, что создалась запись с заданным слагом
        comment = Comment.objects.latest('created')

        self.assertEqual(comment.text, form_data['text'])

    def test_create_comment_by_guest_client(self):
        """
        Проверка возможности создания коммента анонимным пользователем.
        """

        # Считаем количество записей в базе
        comment_count = Comment.objects.count()

        # отправляем новые данные
        form_data = {
            'text': f'{self.comment.text}-гость',
        }

        response = self.guest_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.new_post.pk}),
            data=form_data,
            follow=True,
        )

        # Количество записей в базе не изменилось
        self.assertEqual(Post.objects.count(), comment_count)

        self.assertRedirects(
            response, f'/auth/login/?next=/posts/{self.new_post.pk}/comment/'
        )

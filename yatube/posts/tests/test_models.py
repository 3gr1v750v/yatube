from django.contrib.auth import get_user_model
from django.test import TestCase
from posts.models import Comment, Group, Post

User = get_user_model()


class DataBaseRecords(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(
            username='abcUser',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='T' * 20,
        )
        cls.comment = Comment.objects.create(
            author=cls.user,
            post=cls.post,
            text="Тестовый комментарий",
        )


class PostModelTest(DataBaseRecords):
    def test_post_model_has_correct_object_names(self):
        """Тестирование __str__ модели post."""

        post = PostModelTest.post
        expected_object_name_post = post.text[:15]
        self.assertEqual(expected_object_name_post, str(post))

    def test_post_verbose_name(self):
        """verbose_name в полях модели Post совпадает с ожидаемым."""

        field_verboses = {
            'text': 'Текст сообщения',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа',
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    self.post._meta.get_field(field).verbose_name,
                    expected_value,
                )

    def test_post_help_text(self):
        """help_text в полях модели Post совпадает с ожидаемым."""

        field_help_texts = {
            'text': 'Введите текст для публикации поста',
            'pub_date': 'Введите дату публикации поста',
            'author': 'Автор публикации записи',
            'group': 'Выберети группу для публикации',
        }
        for field, expected_value in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    self.post._meta.get_field(field).help_text, expected_value
                )


class GroupModelTest(DataBaseRecords):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )

    def test_group_model_has_correct_object_names(self):
        """Тестирование __str__ модели group."""

        expected_object_name_group = self.group.title
        self.assertEqual(expected_object_name_group, str(self.group))

    def test_group_verbose_name(self):
        """verbose_name в полях модели Group совпадает с ожидаемым."""

        field_verboses = {
            'title': 'Название группы',
            'slug': 'Метка группы',
            'description': 'Описание группы',
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    self.group._meta.get_field(field).verbose_name,
                    expected_value,
                )

    def test_group_help_text(self):
        """help_text в полях модели Group совпадает с ожидаемым."""

        field_help_texts = {
            'title': 'Введите название группы',
            'slug': 'Введите метку группы',
            'description': 'Введите описание группы',
        }
        for field, expected_value in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    self.group._meta.get_field(field).help_text, expected_value
                )


class CommentsModelTest(DataBaseRecords):
    def test_comment_verbose_name(self):
        """verbose_name в полях модели Comment совпадает с ожидаемым."""

        field_verboses = {
            'post': 'Ссылка на пост',
            'author': 'Автор',
            'text': 'Текст комментария',
            'created': 'Дата публикации',
        }

        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    self.comment._meta.get_field(field).verbose_name,
                    expected_value,
                )

    def test_comment_help_text(self):
        """help_text в полях модели Comment совпадает с ожидаемым."""

        field_help_texts = {
            'text': 'Введите текст для публикации комментария',
        }
        for field, expected_value in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    self.comment._meta.get_field(field).help_text,
                    expected_value,
                )

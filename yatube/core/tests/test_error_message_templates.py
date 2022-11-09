from django.test import TestCase


class ViewTestClass(TestCase):
    def test_error_page(self):
        """
        Проверка, что статус ответа сервера на ошибку 404 правильный
        и используется соответствующий темлпейт.
        """
        response = self.client.get('/nonexist-page/')
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, 'core/404.html')
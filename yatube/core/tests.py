from http import HTTPStatus
from django.test import Client, TestCase


class NotFoundPageTest(TestCase):

    def setUp(self):
        self.user_client = Client()

    def test_not_found_page(self):
        response = self.user_client.get('page_result/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, 'core/404.html')

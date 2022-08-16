from django.test import TestCase, Client

staticPagesList = [
    'author/',
    'tech/',
]


class StaticPageTest(TestCase):
    def setUp(self):
        """Создаем неавторизованный пользователь"""
        self.guest_client = Client()

    # Проверяем общедоступные страницы
    def test_home_url_exists_at_desired_location(self):
        """Страница / доступна любому пользователю."""
        response = self.guest_client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_added_url_exists_at_desired_location(self):
        """Страница из списка staticPagesList -> доступна любому пользователю.
        """
        for staticPage in staticPagesList:
            response = self.guest_client.get(f'/about/{staticPage}')
            self.assertEqual(response.status_code, 200)

from django.test import TestCase, Client
from django.urls import reverse
from .api_client import get_weather_info

class WeatherAppTests(TestCase):
    def setUp(self):
        self.client = Client()

    # Тест на работоспособность вьюшки
    def test_main_view_with_valid_city(self):
        response = self.client.post(reverse('main'), {'city': 'Москва'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Город: Москва')
        self.assertContains(response, 'Текущая погода')

    # Тест на метод get_weather_info
    def test_get_weather_info(self):
        city = 'Москва'
        weather_info = get_weather_info(city)
        self.assertIn('City', weather_info)
        self.assertIn('Timezone', weather_info)
        self.assertIn('Current Weather', weather_info)
        self.assertIn('Weekly Forecast', weather_info)
        self.assertEqual(weather_info['City'], city)

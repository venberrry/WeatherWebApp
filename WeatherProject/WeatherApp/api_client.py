import diskcache as dc
import requests
import openmeteo_requests
from retry_requests import retry
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

city_api_url = f'https://geocoding-api.open-meteo.com/v1/search'
forecast_api_url = "https://api.open-meteo.com/v1/forecast"

# Настройка кэша
cache = dc.Cache('.cache')
retry_session = retry(requests.Session(), retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)

def get_city_coordinates(city):
    # Получаем координаты города по геоапи
    params = {
        "name": city,
        "count": 1,
        "language": "ru",
        "format": "json"
    }

    response_geo = retry_session.get(city_api_url, params=params).json()

    lat = response_geo['results'][0]['latitude']
    lon = response_geo['results'][0]['longitude']

    return lat, lon

def get_weather(city):
    # Проверка наличия данных о погоде в кэше по названию города
    cache_key = f"weather_{city}"
    cached_response = cache.get(cache_key)

    if cached_response:
        logger.info(f"Данные для города {city} получены из кэша")
        response_data = cached_response
    else:
        logger.info(f"Данные для города {city} не найдены в кэше. Запрос новых данных")
        # Получаем координаты города, если нет данных в кэше
        lat, lon = get_city_coordinates(city)

        # Получаем погоду по координатам
        params = {
            "latitude": lat,
            "longitude": lon,
            "current_weather": "true",
            "daily": ["temperature_2m_max", "temperature_2m_min", "rain_sum", "wind_speed_10m_max"],
            "wind_speed_unit": "ms",
            "timezone": "Europe/Moscow"
        }
        responses = openmeteo.weather_api(forecast_api_url, params=params)
        response = responses[0]

        # Формируем ежедневную погоду на неделю для кэша
        daily = response.Daily()
        daily_data = {
            "date": pd.date_range(
                start=pd.to_datetime(daily.Time(), unit="s", utc=True),
                end=pd.to_datetime(daily.TimeEnd(), unit="s", utc=True),
                freq=pd.Timedelta(seconds=daily.Interval()),
                inclusive="left"
            ),
            "temperature_2m_max": daily.Variables(0).ValuesAsNumpy(),
            "temperature_2m_min": daily.Variables(1).ValuesAsNumpy(),
            "rain_sum": daily.Variables(2).ValuesAsNumpy(),
            "wind_speed_10m_max": daily.Variables(3).ValuesAsNumpy()
        }
        # Формируем данные для кэша
        response_data = {
            "city": city,
            "latitude": response.Latitude(),
            "longitude": response.Longitude(),
            "timezone": response.Timezone(),
            "timezone_abbreviation": response.TimezoneAbbreviation(),
            "current_weather": {
                "temperature": response.Current().Variables(0).Value(),
                "rain": response.Current().Variables(1).Value(),
                "windspeed": response.Current().Variables(2).Value()
            },
            "daily": daily_data
        }

        # Сохранение данных в кэш по названию города
        cache.set(cache_key, response_data, expire=60)
        logger.info(f"Данные для города {city} сохранены в кэш.")
    return response_data


# Причёсываем данные погоды
def format_weather_data(response_data):
    timezone = response_data['timezone'].decode('utf-8') + response_data['timezone_abbreviation'].decode('utf-8')

    current_weather_info = {
        "Temperature": round(response_data["current_weather"]["temperature"], 1),
        "Rain": round(response_data["current_weather"].get("rain", 0)),
        "Wind Speed": round(response_data["current_weather"]["windspeed"])
    }

    weekly_forecast_data = {
        "Date": response_data["daily"]["date"],
        "Max Temperature": response_data["daily"]["temperature_2m_max"],
        "Min Temperature": response_data["daily"]["temperature_2m_min"],
        "Rain Sum": response_data["daily"]["rain_sum"],
        "Max Wind Speed": response_data["daily"]["wind_speed_10m_max"]
    }
    weekly_forecast_df = pd.DataFrame(weekly_forecast_data)

    weather_info = {
        "City": response_data["city"],
        "Timezone": timezone,
        "Current Weather": current_weather_info,
        "Weekly Forecast": weekly_forecast_df
    }
    return weather_info

def get_weather_info(city):
    response_data = get_weather(city)
    weather_info = format_weather_data(response_data)
    return weather_info
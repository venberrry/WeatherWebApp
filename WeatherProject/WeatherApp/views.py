from django.shortcuts import render
from .api_client import get_weather_info

def main(request):
    context = {}
    if request.method == 'POST':
        city = request.POST.get('city')
        if city:
            weather_data = get_weather_info(city)
            weekly_forecast_html = weather_data['Weekly Forecast'].to_html(index=False)

            context = {
                'city': weather_data['City'],
                'timezone': weather_data['Timezone'],
                'current_weather': weather_data['Current Weather'],
                'weekly_forecast': weekly_forecast_html
            }
    return render(request, 'main.html', context)

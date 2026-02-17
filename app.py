from flask import Flask, jsonify, render_template, request
import requests

#  Flask → creates the web server
#  jsonify → converts Python dictionary → JSON response
# render_template → loads HTML file
# requests → fetches weather data from the internet

app = Flask(__name__)
#create the webserver

def get_weather(lat, lon):

    weather_url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}"
        f"&current=temperature_2m,relative_humidity_2m,rain"
    )

    air_url = (
        f"https://air-quality-api.open-meteo.com/v1/air-quality?"
        f"latitude={lat}&longitude={lon}"
        f"&current=us_aqi"
    )

    weather_data = requests.get(weather_url).json()
    air_data = requests.get(air_url).json()

    current = weather_data["current"]
    air_current = air_data["current"]

    return {
        "temperature": current["temperature_2m"],
        "humidity": current["relative_humidity_2m"],
        "rain": current["rain"],
        "air_quality": air_current["us_aqi"]
    }
import requests

def get_sun_times(lat, lon):
    url = f"https://api.sunrisesunset.io/json?lat={lat}&lng={lon}"

    data = requests.get(url).json()

    results = data["results"]

    return {
        "sunrise": results["sunrise"],
        "sunset": results["sunset"],
        "day_length": results["day_length"]
    }


cities = {
    "naokothi": (25.4539, 86.1208),
    "northcarolina": (35.7796, -78.6382)
}

# API route
@app.route("/weather/<city>")
def weather(city):
    if city not in cities:
        return jsonify({"error": "City not found"}), 404

    lat, lon = cities[city]

    weather_data = get_weather(lat, lon)
    sun_data = get_sun_times(lat, lon)

    # merge dictionaries
    combined = {**weather_data, **sun_data}

    return jsonify(combined)
@app.route("/live-weather")
def live_weather():
    lat = request.args.get("lat")
    lon = request.args.get("lon")

    weather_data = get_weather(lat, lon)
    sun_data = get_sun_times(lat, lon)

    combined = {**weather_data, **sun_data}

    return jsonify(combined)



# webpage route
@app.route("/")
def home():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)

from flask import Flask, jsonify, render_template, request
import requests
import pandas as pd
import joblib
from datetime import datetime
from math import sin, cos, pi

app = Flask(__name__)

# Load trained ML model
model = joblib.load("models/next_hour_temperature_model.pkl")

# City coordinates
CITIES = {
    "naokothi": (25.4539, 86.1208),
    "northcarolina": (35.7796, -78.6382)
}

# Prepare features for ML model
def prepare_input(weather_data):
    now = datetime.now()
    month = now.month
    hour = now.hour

    month_sin = sin(2 * pi * month / 12)
    month_cos = cos(2 * pi * month / 12)
    hour_sin = sin(2 * pi * hour / 24)
    hour_cos = cos(2 * pi * hour / 24)

    df_input = pd.DataFrame([{
        "Temperature (C)": weather_data.get("temperature", 0),
        "Apparent Temperature (C)": weather_data.get("temperature", 0),
        "Humidity": weather_data.get("humidity", 0),
        "Wind Speed (km/h)": weather_data.get("wind_speed", 0),
        "Wind Bearing (degrees)": weather_data.get("wind_bearing", 0),
        "Visibility (km)": weather_data.get("visibility", 0),
        "Loud Cover": weather_data.get("cloud_cover", 0),
        "Pressure (millibars)": weather_data.get("pressure", 0),
        "year": now.year,
        "month": month,
        "day": now.day,
        "hour": hour,
        "month_sin": month_sin,
        "month_cos": month_cos,
        "hour_sin": hour_sin,
        "hour_cos": hour_cos
    }])
    return df_input

# Predict next hour temperature
def predict_next_hour(weather_data):
    df_input = prepare_input(weather_data)
    prediction = model.predict(df_input)[0]
    return round(float(prediction), 2)

# Fetch current weather from Open-Meteo
def get_weather(lat, lon):
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}"
        f"&current=temperature_2m,relative_humidity_2m,rain,"
        f"wind_speed_10m,pressure_msl"
    )
    data = requests.get(url).json()
    current = data.get("current", {})
    return {
        "temperature": current.get("temperature_2m", 0),
        "humidity": current.get("relative_humidity_2m", 0),
        "rain": current.get("rain", 0),
        "wind_speed": current.get("wind_speed_10m", 0),
        "pressure": current.get("pressure_msl", 0)
    }

# Fetch sunrise/sunset
def get_sun_times(lat, lon):
    url = f"https://api.sunrisesunset.io/json?lat={lat}&lng={lon}"
    data = requests.get(url).json()
    results = data.get("results", {})
    return {
        "sunrise": results.get("sunrise", "N/A"),
        "sunset": results.get("sunset", "N/A")
    }

# API route for a city
@app.route("/weather/<city>")
def weather(city):
    if city not in CITIES:
        return jsonify({"error": "City not found"}), 404

    lat, lon = CITIES[city]
    weather_data = get_weather(lat, lon)
    sun_data = get_sun_times(lat, lon)
    next_hour_temp = predict_next_hour(weather_data)
    combined = {**weather_data, **sun_data, "next_hour_prediction": next_hour_temp}
    return jsonify(combined)

# API route for live location
@app.route("/live-weather")
def live_weather():
    lat = request.args.get("lat", type=float)
    lon = request.args.get("lon", type=float)
    if lat is None or lon is None:
        return jsonify({"error": "Latitude and longitude required"}), 400

    weather_data = get_weather(lat, lon)
    sun_data = get_sun_times(lat, lon)
    next_hour_temp = predict_next_hour(weather_data)
    combined = {**weather_data, **sun_data, "next_hour_prediction": next_hour_temp}
    return jsonify(combined)

# Home page
@app.route("/")
def home():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
from flask import Flask, jsonify, render_template, request
import requests
import pandas as pd
import joblib
from datetime import datetime, timedelta
from math import sin, cos, pi

app = Flask(__name__)

# Load trained ML model
model = joblib.load("models/next_hour_temperature_model.pkl")

CITIES = {
    "naokothi": (25.4539, 86.1208),
    "raleigh": (35.7796, -78.6382)
}

def prepare_input(weather_data):
    now = datetime.now()
    df_input = pd.DataFrame([{
        "Temperature (C)": weather_data.get("temperature", 0),
        "Apparent Temperature (C)": weather_data.get("temperature", 0),
        "Humidity": weather_data.get("humidity", 0),
        "Wind Speed (km/h)": weather_data.get("wind_speed", 0),
        "Wind Bearing (degrees)": 0,
        "Visibility (km)": 10,
        "Loud Cover": 0,
        "Pressure (millibars)": 1013,
        "year": now.year, "month": now.month, "day": now.day, "hour": now.hour,
        "month_sin": sin(2 * pi * now.month / 12),
        "month_cos": cos(2 * pi * now.month / 12),
        "hour_sin": sin(2 * pi * now.hour / 24),
        "hour_cos": cos(2 * pi * now.hour / 24)
    }])
    return df_input

def get_aqi(lat, lon):
    try:
        url = f"https://air-quality-api.open-meteo.com/v1/air-quality?latitude={lat}&longitude={lon}&current=us_aqi"
        data = requests.get(url).json()
        return data.get("current", {}).get("us_aqi", "N/A")
    except:
        return "N/A"

def get_weather(lat, lon):
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}"
        f"&current=temperature_2m,relative_humidity_2m,apparent_temperature,wind_speed_10m,weather_code"
        f"&hourly=temperature_2m,weather_code&daily=temperature_2m_max,temperature_2m_min,weather_code&timezone=auto"
    )
    data = requests.get(url).json()
    current = data.get("current", {})
    
    hourly = [{"time": (datetime.now() + timedelta(hours=i)).strftime("%-I%p"), 
               "temp": round(data["hourly"]["temperature_2m"][i]), 
               "code": data["hourly"]["weather_code"][i]} for i in range(24)]

    days = ["Today", "Fri", "Sat", "Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    daily = [{"day": days[i], "low": round(data["daily"]["temperature_2m_min"][i]), 
              "high": round(data["daily"]["temperature_2m_max"][i]), 
              "code": data["daily"]["weather_code"][i]} for i in range(7)]

    return {
        "temperature": round(current.get("temperature_2m", 0)),
        "feels_like": round(current.get("apparent_temperature", 0)),
        "humidity": current.get("relative_humidity_2m", 0),
        "wind_speed": current.get("wind_speed_10m", 0),
        "current_code": current.get("weather_code", 0),
        "hourly": hourly,
        "daily": daily
    }

@app.route("/weather/<city>")
def weather(city):
    lat, lon = CITIES.get(city.lower(), (35.7796, -78.6382))
    w_data = get_weather(lat, lon)
    w_data["aqi"] = get_aqi(lat, lon)
    w_data["next_hour_prediction"] = predict_next_hour(w_data)
    w_data["city_name"] = city.capitalize()
    return jsonify(w_data)

@app.route("/live-weather")
def live_weather():
    lat, lon = request.args.get("lat", type=float), request.args.get("lon", type=float)
    w_data = get_weather(lat, lon)
    w_data["aqi"] = get_aqi(lat, lon)
    w_data["next_hour_prediction"] = predict_next_hour(w_data)
    w_data["city_name"] = "My Location"
    return jsonify(w_data)

@app.route("/")
def home():
    return render_template("index.html")

def predict_next_hour(weather_data):
    df_input = prepare_input(weather_data)
    prediction = model.predict(df_input)[0]
    return round(float(prediction), 1)

if __name__ == "__main__":
    app.run(debug=True)
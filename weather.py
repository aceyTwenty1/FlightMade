import requests

def get_launch_weather(lat, lon):
    """
    Fetches live weather data for the launch site and converts 
    values to standard SI units for the physics engine.
    """
    # Open-Meteo API endpoint asking for surface pressure, temp, and wind
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,surface_pressure,wind_speed_10m,wind_direction_10m&wind_speed_unit=ms"
    
    try:
        response = requests.get(url)
        response.raise_for_status() # Raise an error if the request failed
        data = response.json()["current"]
        
        # Open-Meteo gives pressure in hPa, convert to Pascals (Pa) for physics
        surface_pressure_pa = data["surface_pressure"] * 100
        
        # Convert Celsius to Kelvin
        temperature_k = data["temperature_2m"] + 273.15
        
        # Calculate initial air density (rho) using the ideal gas law: P / (R * T)
        # Specific gas constant for dry air is ~287.05 J/(kg·K)
        air_density = surface_pressure_pa / (287.05 * temperature_k)
        
        weather_profile = {
            "temperature_k": temperature_k,
            "pressure_pa": surface_pressure_pa,
            "air_density_rho0": air_density,
            "wind_speed_ms": data["wind_speed_10m"],      # Already in m/s
            "wind_direction_deg": data["wind_direction_10m"] # 0-360 degrees
        }
        
        return weather_profile

    except Exception as e:
        print(f"Error fetching weather data: {e}")
        return None

# Quick test to make sure it works (Using Cape Canaveral coordinates)
if __name__ == "__main__":
    cape_canaveral_lat = 28.3922
    cape_canaveral_lon = -80.6077
    
    print("Fetching live weather for Cape Canaveral...")
    weather = get_launch_weather(cape_canaveral_lat, cape_canaveral_lon)
    
    if weather:
        print("\n--- Launch Pad Weather Profile ---")
        for key, value in weather.items():
            print(f"{key}: {value:.2f}")
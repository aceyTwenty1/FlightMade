import math
import json
import weather
import physics

def meters_to_lat_lon(start_lat, start_lon, delta_x_meters, delta_y_meters):
    meters_per_degree_lat = 111132.92
    meters_per_degree_lon = 111412.84 * math.cos(math.radians(start_lat))
    new_lat = start_lat + (delta_y_meters / meters_per_degree_lat)
    new_lon = start_lon + (delta_x_meters / meters_per_degree_lon)
    return new_lat, new_lon

def generate_czml(flight_data, start_lat, start_lon):
    czml = [
        {
            "id": "document",
            "name": "Rocket Simulation Telemetry",
            "version": "1.0"
        }
    ]
    
    rocket_packet = {
        "id": "rocket_path",
        "name": "Live Sim Trajectory",
        "availability": "2026-06-23T12:00:00Z/2026-06-23T12:10:00Z",
        "path": {
            "material": {"solidColor": {"color": {"rgba": [255, 69, 0, 255]}}},
            "width": 4,
            "leadTime": 0,
            "trailTime": 600,
            "resolution": 1
        },
        "position": {
            "epoch": "2026-06-23T12:00:00Z",
            "cartographicDegrees": []
        }
    }
    
    for step in flight_data[::2]:  
        lat, lon = meters_to_lat_lon(start_lat, start_lon, step["x"], step["y"])
        rocket_packet["position"]["cartographicDegrees"].extend([
            step["time"], lon, lat, step["z"]
        ])
        
    czml.append(rocket_packet)
    return czml

def main():
    launch_sites = {
        "1": {"name": "Cape Canaveral, USA (NASA/SpaceX)", "lat": 28.3922, "lon": -80.6077},
        "2": {"name": "Vandenberg, USA (Polar Launches)", "lat": 34.7420, "lon": -120.5724},
        "3": {"name": "Guiana Space Centre, French Guiana (ESA)", "lat": 5.2363, "lon": -52.7680},
        "4": {"name": "Baikonur Cosmodrome, Kazakhstan (Roscosmos)", "lat": 45.9650, "lon": 63.3050},
        "5": {"name": "Mahia Peninsula, New Zealand (Rocket Lab)", "lat": -39.2614, "lon": 177.8646}
    }
    
    print("=============================================")
    print("        REACTIVE ROCKET LAUNCH SYSTEM        ")
    print("=============================================\n")
    
    print("Select your launch location:")
    for key, site in launch_sites.items():
        print(f"  [{key}] {site['name']}")
    print("  [6] Enter Custom Coordinates")
    
    choice = input("\nChoose an option (1-6): ").strip()
    
    if choice in launch_sites:
        selected = launch_sites[choice]
        launch_lat = selected["lat"]
        launch_lon = selected["lon"]
        print(f"\nSelected: {selected['name']}")
    elif choice == "6":
        try:
            launch_lat = float(input("Enter Latitude (-90 to 90): "))
            launch_lon = float(input("Enter Longitude (-180 to 180): "))
        except ValueError:
            print("Invalid numbers. Defaulting to Cape Canaveral.")
            launch_lat, launch_lon = 28.3922, -80.6077
    else:
        print("Invalid choice. Defaulting to Cape Canaveral.")
        launch_lat, launch_lon = 28.3922, -80.6077

    try:
        print("\nSet Flight Trajectory Profile:")
        launch_azimuth = float(input("  Enter Launch Heading (0=North, 90=East, 180=South, 270=West): "))
        launch_angle = float(input("  Enter Pitch Launch Angle (45 to 90 degrees from ground): "))
    except ValueError:
        print("Invalid inputs. Defaulting to Azimuth 90 (East), Angle 85.")
        launch_azimuth, launch_angle = 90.0, 85.0

    print("\n--- STEP 1: Fetching Live Environmental Weather Assets ---")
    
    # FIX: Added automatic offline fallback if internet drops
    try:
        live_weather = weather.get_launch_weather(launch_lat, launch_lon)
    except Exception:
        live_weather = None

    if not live_weather:
        print("  [!] Direct API connection unavailable. Loading baseline standard atmosphere fallback...")
        live_weather = {
            "temperature_k": 288.15,
            "air_density_rho0": 1.225,
            "wind_speed_ms": 0.0,
            "wind_direction_deg": 0.0
        }
        
    print(f"  Surface Temperature: {live_weather['temperature_k'] - 273.15:.1f}°C")
    print(f"  Surface Air Density: {live_weather['air_density_rho0']:.4f} kg/m³")
    print(f"  Live Wind Vector: {live_weather['wind_speed_ms']:.2f} m/s blowing from {live_weather['wind_direction_deg']}°")

    print("\n--- STEP 2: Running Multi-Layer Atmospheric Physics Engine ---")
    flight_data = physics.calculate_trajectory(live_weather, launch_azimuth, launch_angle)
    
    # DIAGNOSTIC PRINT: Let's see if your physics engine is actually calculating anything
    print(f"  [DIAGNOSTIC] Physics engine returned {len(flight_data)} frames of data.")
    if len(flight_data) > 0:
        print(f"  [DIAGNOSTIC] First data point: {flight_data[0]}")
        print(f"  [DIAGNOSTIC] Max Altitude calculated: {max(step['z'] for step in flight_data):.2f} meters.")
    else:
        print("  [WARNING] physics.calculate_trajectory returned an EMPTY list! Telemetry will be zero.")

    print("\n--- STEP 3: Compiling Telemetry Databases ---")
    czml_data = generate_czml(flight_data, launch_lat, launch_lon)
    
    with open("trajectory.czml", "w") as f:
        json.dump(czml_data, f, indent=2)
        
    with open("telemetry.json", "w") as f:
        json.dump(flight_data, f, indent=2)
        
    print("\n=============================================")
    print("SIMULATION COMPLETE: Data pipelines updated.")
    print("Refresh your browser window to witness the flight.")
    print("=============================================")

if __name__ == "__main__":
    main()
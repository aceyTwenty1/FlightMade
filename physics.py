import math

def get_atmosphere_density(altitude_m, weather):
    """
    Calculates air density across all major atmospheric layers 
    using piece-wise lapse rates anchored to live surface data.
    """
    # Constants
    g0 = 9.80665
    R = 287.05  # Specific gas constant for air
    
    # Base surface conditions from our live API call
    T_prev = weather["temperature_k"]
    P_prev = weather["pressure_pa"]
    h_prev = 0.0
    
    # Define standard atmosphere layers: (Ceiling Altitude in meters, Lapse Rate K/m)
    layers = [
        (11000, -0.0065),  # Troposphere
        (20000,  0.0),     # Tropopause / Lower Stratosphere
        (32000,  0.0010),  # Mid Stratosphere
        (47000,  0.0028),  # Upper Stratosphere
        (51000,  0.0),     # Stratopause
        (71000, -0.0028),  # Mesosphere
        (84852, -0.0020)   # Upper Mesosphere / Mesopause
    ]
    
    # Beyond 84.85km (Thermosphere / Space), air density is negligible for drag
    if altitude_m > 84852:
        return 0.0

    # Step up through the layers to find where the rocket currently is
    for h_ceiling, lapse_rate in layers:
        # Determine the top altitude of our current evaluation block
        h_current = min(altitude_m, h_ceiling)
        dh = h_current - h_prev
        
        if lapse_rate != 0:
            T_curr = T_prev + lapse_rate * dh
            # Pressure formula for changing temperature
            P_curr = P_prev * (T_prev / T_curr) ** (g0 / (R * lapse_rate))
        else:
            T_curr = T_prev
            # Pressure formula for constant temperature (isothermal)
            P_curr = P_prev * math.exp(-g0 * dh / (R * T_prev))
            
        # If we reached the rocket's altitude, stop calculating layers
        if altitude_m <= h_ceiling:
            return P_curr / (R * T_curr)
            
        # Move up to the next layer baseline
        T_prev = T_curr
        P_prev = P_curr
        h_prev = h_current

    return 0.0


def calculate_trajectory(weather, azimuth_deg, launch_angle_deg):
    """
    Simulates rocket flight path in 3D across all atmospheric layers.
    """
    # --- Rocket Specs (Falcon 9-ish Medium Lift) ---
    dry_mass = 25000.0      # kg
    fuel_mass = 400000.0    # kg
    thrust = 7600000.0      # Newtons
    burn_rate = 2500.0      # kg/s
    cd = 0.50               # Drag coefficient
    cross_area = 10.5       # m^2 (Diameter ~3.7m)
    
    dt = 0.1  # 10 physics updates per second
    time = 0.0
    x, y, z = 0.0, 0.0, 0.0  # x=East, y=North, z=Altitude
    vx, vy, vz = 0.0, 0.0, 0.0
    
    # Directions
    azimuth_rad = math.radians(azimuth_deg)
    launch_rad = math.radians(launch_angle_deg)
    dir_z = math.sin(launch_rad)
    dir_x = math.cos(launch_rad) * math.sin(azimuth_rad)
    dir_y = math.cos(launch_rad) * math.cos(azimuth_rad)
    
    # Wind Profile
    wind_to_rad = math.radians((weather["wind_direction_deg"] + 180) % 360)
    wind_speed = weather["wind_speed_ms"]
    wind_vx = wind_speed * math.sin(wind_to_rad)
    wind_vy = wind_speed * math.cos(wind_to_rad)
    
    trajectory_log = []
    
    while z >= 0:
        current_mass = dry_mass + fuel_mass
        is_burning = fuel_mass > 0
        
        if is_burning:
            fuel_mass -= burn_rate * dt
            if fuel_mass < 0: fuel_mass = 0
            
        # Use our new upgraded multi-layer atmosphere calculation
        rho = get_atmosphere_density(z, weather)
        
        # Relative Velocity to Wind
        rel_vx, rel_vy, rel_vz = (vx - wind_vx), (vy - wind_vy), vz
        v_rel_mag = math.sqrt(rel_vx**2 + rel_vy**2 + rel_vz**2)
        
        # Thrust vectors
        v_mag = math.sqrt(vx**2 + vy**2 + vz**2)
        if v_mag > 0:
            tx, ty, tz = vx / v_mag, vy / v_mag, vz / v_mag
        else:
            tx, ty, tz = dir_x, dir_y, dir_z
            
        f_thrust_x = thrust * tx if is_burning else 0
        f_thrust_y = thrust * ty if is_burning else 0
        f_thrust_z = thrust * tz if is_burning else 0
        
        # Drag force
        if v_rel_mag > 0 and rho > 0:
            drag_mag = 0.5 * rho * (v_rel_mag**2) * cd * cross_area
            f_drag_x = -drag_mag * (rel_vx / v_rel_mag)
            f_drag_y = -drag_mag * (rel_vy / v_rel_mag)
            f_drag_z = -drag_mag * (rel_vz / v_rel_mag)
        else:
            f_drag_x = f_drag_y = f_drag_z = 0
            
        # Gravity
        f_grav_z = -current_mass * 9.81
        
        # Net forces
        ax = (f_thrust_x + f_drag_x) / current_mass
        ay = (f_thrust_y + f_drag_y) / current_mass
        az = (f_thrust_z + f_drag_z + f_grav_z) / current_mass
        
        # Step values
        vx += ax * dt; vy += ay * dt; vz += az * dt
        x += vx * dt; y += vy * dt; z += vz * dt
        time += dt
        
        trajectory_log.append({"time": time, "x": x, "y": y, "z": z})
        
        # Built-in safety caps
        if time > 600.0 or math.sqrt(x**2 + y**2) > 1000000:
            break
            
    return trajectory_log
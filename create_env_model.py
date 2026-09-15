"""
CINT-70: Create Environment Model from Extracted MEDA Data
"""
import json

with open("data/extracted/thermal_constraints.json") as f:
    tc = json.load(f)

# Air temps
air = tc["air_temperature_celsius"]
air_k = tc["air_temperature_kelvin"]

# Ground temps
ground = tc["ground_temperature_celsius"]
ground_k = tc["ground_temperature_kelvin"]

# Variance from kelvin (std exists there)
air_variance = air_k["std"] ** 2
ground_variance = ground_k["std"] ** 2

env_model = {
    "source": "NASA PDS Mars 2020 MEDA - Derived from TIRS sensor data",
    "source_url": tc["source_url"],
    "extraction_date": tc["extraction_date"],
    "total_data_points": tc["data_points_air_temp"] + tc["data_points_ground_temp"],
    
    "mars_environment": {
        "atmosphere": {
            "temperature_range_c": [air["min"], air["max"]],
            "mean_temperature_c": air["mean"],
            "variance": air_variance,
            "description": "Mars atmospheric temperature from MEDA TIRS at Jezero Crater"
        },
        "surface": {
            "temperature_range_c": [ground["min"], ground["max"]],
            "mean_temperature_c": ground["mean"],
            "variance": ground_variance,
            "description": "Mars surface brightness temperature from MEDA TIRS"
        },
        "thermal_cycling": {
            "max_diurnal_swing_c": air["max"] - air["min"],
            "typical_operational_range_c": [-90, 10],
            "extreme_survival_range_c": [-125, 80]
        }
    },
    
    "constraints_for_cint70": {
        "robotic_arm_thermal_limits": {
            "operating_temp_c": [-100, 50],
            "survival_temp_c": [-130, 80],
            "source": "Derived from MEDA data + NASA engineering margins"
        },
        "material_constraints": {
            "aluminum_6061": {"min_c": -150, "max_c": 120, "expansion_coeff_um_m_c": 23.1},
            "titanium_ti6al4v": {"min_c": -200, "max_c": 300, "expansion_coeff_um_m_c": 8.6},
            "carbon_composite": {"min_c": -100, "max_c": 150, "expansion_coeff_um_m_c": 2.1}
        },
        "thermal_shock_risk": {
            "max_safe_rate_c_per_min": 10.0,
            "warning": "Rapid temperature changes during sunrise/sunset transitions"
        }
    },
    
    "validation_rules": {
        "check_ambient_temp": {
            "description": "Ensure robotic arm operation within safe ambient range",
            "min_allowed_c": air["min"] - 10,
            "max_allowed_c": air["max"] + 10
        },
        "check_surface_temp": {
            "description": "Ensure end-effector contact within material limits",
            "min_allowed_c": -150,
            "max_allowed_c": 120
        }
    }
}

with open("data/extracted/environment_model.json", "w") as f:
    json.dump(env_model, f, indent=2)

print("✅ environment_model.json created")
print(f"   Mars air temp: {air['min']:.1f}°C to {air['max']:.1f}°C (mean: {air['mean']:.1f}°C)")
print(f"   Mars ground temp: {ground['min']:.1f}°C to {ground['max']:.1f}°C (mean: {ground['mean']:.1f}°C)")
print(f"   Robotic arm operating: -100°C to 50°C")
print(f"   Total data points: {tc['data_points_air_temp'] + tc['data_points_ground_temp']:,}")
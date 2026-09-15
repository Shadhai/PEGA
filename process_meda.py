"""
CINT-70: Process Mars 2020 MEDA Data - FIXED PARSER
Extracts AIR_TEMP and GROUND_TEMP from real CSV columns
"""
import csv
import json
import os
import numpy as np
from pathlib import Path

BASE_DIR = Path("mars2020_meda")
CALIBRATED_DIR = BASE_DIR / "data_calibrated_env" / "sol_0000_0089"
DERIVED_EARLY = BASE_DIR / "data_derived_env" / "sol_0000_0089"
DERIVED_LATER = BASE_DIR / "data_derived_env" / "sol_1620_1739"
OUTPUT_DIR = Path("data/extracted")

def extract_temps(data_dir, label):
    """Extract AIR_TEMP (col 5) and GROUND_TEMP (col 11) from TIRS CSV files"""
    air_temps = []
    ground_temps = []
    sol_count = 0
    
    for sol_dir in sorted(data_dir.iterdir()):
        if not sol_dir.is_dir():
            continue
        
        sol_count += 1
        for csv_file in sol_dir.glob("*TIRS*.CSV"):
            try:
                with open(csv_file) as f:
                    reader = csv.reader(f)
                    header = next(reader, None)  # Skip header
                    
                    for row in reader:
                        if len(row) >= 12:
                            try:
                                air_temp = float(row[5])    # AIR_TEMP column
                                ground_temp = float(row[11]) # GROUND_TEMP column
                                
                                if 150 < air_temp < 350:
                                    air_temps.append(air_temp)
                                if 100 < ground_temp < 350:
                                    ground_temps.append(ground_temp)
                            except (ValueError, IndexError):
                                continue
            except Exception as e:
                print(f"    Warning: {csv_file.name}: {e}")
    
    print(f"    {label}: {sol_count} sols, {len(air_temps)} air temps, {len(ground_temps)} ground temps")
    return air_temps, ground_temps

def main():
    print("=" * 60)
    print("CINT-70: MEDA Data Processor (Fixed)")
    print("=" * 60)
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    all_air = []
    all_ground = []
    
    # Process calibrated data
    print("\n[1/3] Processing calibrated data...")
    air, ground = extract_temps(CALIBRATED_DIR, "Calibrated")
    all_air.extend(air)
    all_ground.extend(ground)
    
    # Process derived early
    print("\n[2/3] Processing derived data...")
    air, ground = extract_temps(DERIVED_EARLY, "Derived Early")
    all_air.extend(air)
    all_ground.extend(ground)
    
    # Process derived later
    air, ground = extract_temps(DERIVED_LATER, "Derived Later")
    all_air.extend(air)
    all_ground.extend(ground)
    
    print(f"\n[3/3] Creating CINT-70 data files...")
    print(f"    Total: {len(all_air)} air temp readings, {len(all_ground)} ground temp readings")
    
    if all_air or all_ground:
        # Thermal Constraints
        thermal_constraints = {
            "source": "NASA PDS Mars 2020 MEDA Bundle - TIRS Sensor",
            "source_url": "https://pds-atmospheres.nmsu.edu/PDS/data/PDS4/Mars2020/mars2020_meda/",
            "extraction_date": "2026-08-06",
            "data_points_air_temp": len(all_air),
            "data_points_ground_temp": len(all_ground),
            "air_temperature_kelvin": {
                "min": float(np.min(all_air)),
                "max": float(np.max(all_air)),
                "mean": float(np.mean(all_air)),
                "std": float(np.std(all_air))
            },
            "air_temperature_celsius": {
                "min": float(np.min(all_air)) - 273.15,
                "max": float(np.max(all_air)) - 273.15,
                "mean": float(np.mean(all_air)) - 273.15
            },
            "ground_temperature_kelvin": {
                "min": float(np.min(all_ground)),
                "max": float(np.max(all_ground)),
                "mean": float(np.mean(all_ground)),
                "std": float(np.std(all_ground))
            },
            "ground_temperature_celsius": {
                "min": float(np.min(all_ground)) - 273.15,
                "max": float(np.max(all_ground)) - 273.15,
                "mean": float(np.mean(all_ground)) - 273.15
            }
        }
        
        with open(OUTPUT_DIR / "thermal_constraints.json", "w") as f:
            json.dump(thermal_constraints, f, indent=2)
        print(f"    ✅ thermal_constraints.json")
        print(f"       Mars Air Temp: {thermal_constraints['air_temperature_celsius']['min']:.1f}°C to {thermal_constraints['air_temperature_celsius']['max']:.1f}°C")
        print(f"       Mars Ground Temp: {thermal_constraints['ground_temperature_celsius']['min']:.1f}°C to {thermal_constraints['ground_temperature_celsius']['max']:.1f}°C")
    
    # Sensor Specs
    sensor_specs = {
        "source": "NASA PDS Mars 2020 MEDA Bundle",
        "instruments": {
            "TIRS": {
                "name": "Thermal Infrared Sensor",
                "channels": 5,
                "measurements": ["DOWNWARD_LW_IRRADIANCE", "AIR_TEMP", "GROUND_TEMP"],
                "air_temp_accuracy_k": 2.12,
                "ground_temp_accuracy_k": 3.80
            }
        }
    }
    
    with open(OUTPUT_DIR / "sensor_specs.json", "w") as f:
        json.dump(sensor_specs, f, indent=2)
    print(f"    ✅ sensor_specs.json")
    
    print(f"\n{'='*60}")
    print(f"✅ PROCESSING COMPLETE")
    print(f"   Files in: {OUTPUT_DIR}/")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
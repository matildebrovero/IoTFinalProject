import random
import neurokit2 as nk

# Global variables to keep track of fever status
fever_periods = [False, True] * 4  # 4 periods of normal temperature and 4 periods with fever
fever_period_index = 0

# FUNCTION TO SIMULATE THE BODY TEMPERATURE
def read_body_temperature():
    global fever_period_index
    
    fever = fever_periods[fever_period_index]
    fever_period_index = (fever_period_index + 1) % len(fever_periods)

    # Simulate body temperature reading
    # Normal human body temperature ranges from 36.1°C to 37.2°C
    # If fever=True, simulate presence of fever with increased temperature
    if fever:
        normal_body_temperature = random.uniform(37.5, 39.0)  # Fever temperature
    else:
        normal_body_temperature = random.uniform(36.1, 37.2)  # Normal temperature
    random_variation = random.uniform(-0.2, 0.2)  # Maximum random variation of ±0.2°C
    body_temperature = normal_body_temperature + random_variation
    # Round the temperature to two decimal places
    body_temperature = round(body_temperature, 2)
    return body_temperature

# Global variables to keep track of blood pressure status
pressure_periods = [False, True] * 4  # 4 periods of normal blood pressure and 4 periods with altered blood pressure
pressure_period_index = 0

# FUNCTION TO SIMULATE THE BLOOD PRESSURE
def read_blood_pressure():
    global pressure_period_index
    
    altered_pressure = pressure_periods[pressure_period_index]
    pressure_period_index = (pressure_period_index + 1) % len(pressure_periods)

    # Simulate blood pressure reading
    # Normal blood pressure ranges from 80 mmHg (diastolic) to 120 mmHg (systolic)
    # If altered_pressure=True, simulate altered blood pressure
    if altered_pressure:
        # Generate altered blood pressure values
        systolic_pressure = random.randint(140, 180)  # High systolic
        diastolic_pressure = random.randint(90, 110)  # High diastolic
    else:
        # Generate normal blood pressure values
        systolic_pressure = random.randint(90, 120)  # Normal systolic
        diastolic_pressure = random.randint(60, 80)  # Normal diastolic
    
    # Create a tuple with blood pressure values
    blood_pressure = (systolic_pressure, diastolic_pressure)
    return blood_pressure

# Global variables to keep track of glucose status
glucose_periods = [False, True] * 4  # 4 periods of normal glucose and 4 periods with altered glucose
glucose_period_index = 0

# FUNCTION TO SIMULATE THE GLUCOSE LEVEL
def read_glucometer():
    global glucose_period_index
    
    altered_glucose = glucose_periods[glucose_period_index]
    glucose_period_index = (glucose_period_index + 1) % len(glucose_periods)

    # Simulate glucose reading
    # Normal glucose levels range from 80 mg/dL to 120 mg/dL
    # If altered_glucose=True, simulate altered glucose
    if altered_glucose:
        # Generate altered glucose values
        glucose_level = random.randint(140, 180)  # High glucose level
    else:
        # Generate normal glucose values
        glucose_level = random.randint(80, 120)  # Normal glucose level
    
    return glucose_level

# Global variables to keep track of oxygenation status
oxygen_periods = [False, True] * 4  # 4 periods of normal oxygenation and 4 periods with altered oxygenation
oxygen_period_index = 0

# FUNCTION TO SIMULATE THE OXYGEN SATURATION
def read_oximeter():
    global oxygen_period_index
    
    altered_oxygen = oxygen_periods[oxygen_period_index]
    oxygen_period_index = (oxygen_period_index + 1) % len(oxygen_periods)

    # Simulate oxygen saturation reading
    # Normal oxygen saturation ranges from 95% to 100%
    # If altered_oxygen=True, simulate altered oxygen saturation
    if altered_oxygen:
        # Generate altered oxygen saturation values
        oxygen_level = random.randint(90, 95)  # Low oxygen saturation level
    else:
        # Generate normal oxygen saturation values
        oxygen_level = random.randint(96, 100)  # Normal oxygen saturation level
    
    return oxygen_level

# Function to generate simulated ECG data
def generate_simulated_ecg(duration=60, sampling_rate=100, noise_level=0.5):
    """
    Function that simulates ECG data.
    """
    ecg_signal = nk.ecg_simulate(duration=duration,sampling_rate=sampling_rate, noise=0.01, heart_rate=80, heart_rate_std=30, method='ecgsyn')

    return ecg_signal.tolist(), sampling_rate

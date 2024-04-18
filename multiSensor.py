import websocket
import json
import numpy as np

# Dictionary to store the latest readings
latest_sensor_data = {
    'android.sensor.gyroscope': None,
    'android.sensor.accelerometer': None,
    'android.sensor.magnetic_field': None,
}

def normalize(v):
    norm = np.linalg.norm(v)
    if norm == 0: 
       return v
    return v / norm


def calculate_pitch_roll(accel):
    ax, ay, az = accel
    pitch = np.arctan2(-ax, np.sqrt(ay**2 + az**2))
    roll = np.arctan2(ay, az)
    return np.degrees(pitch), np.degrees(roll)  # Convert radians to degrees

def calculate_yaw(mag, pitch, roll):
    mx, my, mz = mag
    roll_rad = np.radians(roll)
    pitch_rad = np.radians(pitch)

    # Adjust magnetometer readings
    mx_prime = mx * np.cos(roll_rad) + my * np.sin(pitch_rad) * np.sin(roll_rad) + mz * np.cos(pitch_rad) * np.sin(roll_rad)
    my_prime = my * np.cos(pitch_rad) - mz * np.sin(pitch_rad)

    # Calculate yaw
    yaw = np.arctan2(-my_prime, mx_prime)
    return np.degrees(yaw)  # Convert radians to degrees



def on_message(ws, message):
   
    data = json.loads(message)
    sensor_type = data['type']
    values = data['values']

    # Update the latest readings
    latest_sensor_data[sensor_type] = values

    # Check if all sensors have data
    if all(latest_sensor_data.values()):
        # Calculate orientation
        pitch, roll = calculate_pitch_roll(normalize(np.array(latest_sensor_data['android.sensor.accelerometer'])))
        yaw = calculate_yaw(normalize(np.array(latest_sensor_data['android.sensor.magnetic_field'])), pitch, roll)
        print('Yaw:', yaw, 'Pitch:', pitch, 'Roll:', roll)
        

def on_error(ws, error):
    print("error occurred")
    print(error)

def on_close(ws, close_code, reason):
    print("connection close")
    print("close code : ", close_code)
    print("reason : ", reason  )

def on_open(ws):
    print("connected")
    

def connect(url):
    ws = websocket.WebSocketApp(url,
                              on_open=on_open,
                              on_message=on_message,
                              on_error=on_error,
                              on_close=on_close)

    ws.run_forever()
 

connect('ws://10.0.0.128:8080/sensors/connect?types=["android.sensor.accelerometer","android.sensor.gyroscope","android.sensor.magnetic_field"]')  

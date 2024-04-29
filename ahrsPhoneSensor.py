import json
import numpy as np
import threading
import websocket


class SensorDataHandler:
    def __init__(self, address, sensors, debugLevel=0):
        self.address = address
        self.sensors = sensors
        self.debugLevel = debugLevel
        self.ws = None
        self.callbacks = []
        '''
        {"values":[11.1875,-24.1875,-35.8125],"timestamp":1238531443928498,"accuracy":3,"type":"android.sensor.magnetic_field"}
        {"values":[0.20770179,3.1304858,9.954047],"timestamp":1238531439468498,"accuracy":3,"type":"android.sensor.accelerometer"}
        {"values":[-0.46664867,-0.7470358,0.15627678],"timestamp":1238531440319498,"accuracy":3,"type":"android.sensor.gyroscope"}
        ...

        Sensor data is sent asynchronously in the format above. The data is in JSON format and contains the following fields:
        - values: A list of floating point values representing the sensor data
        - timestamp: The timestamp of the sensor data in nanoseconds
        - accuracy: The accuracy of the sensor data

        The order of the sensor data is not guaranteed and the data may be sent at different rates. The data may also be noisy and may contain outliers.
        We wait for all three sensor data to call the callback function.

        Crete a single datapoint which contains the latest sensory data with the following format:
        {
            'timestamp': 1238531443928498,
            'gyro': [0.20770179,3.1304858,9.954047],
            'accel': [-0.46664867,-0.7470358,0.15627678],
            'mag': [11.1875,-24.1875,-35.8125]
        }

        Don't discard any data, update the latest sensor data with the latest data received.
        https://e2e.ti.com/support/wireless-connectivity/bluetooth-group/bluetooth/f/bluetooth-forum/263264/sensor-tag-synchronize-output-of-accelerometer-gyroscope-and-magnetometer

        '''
        self.latest_sensor_data = {
            'timestamp': 0,
            'gyro': [0, 0, 0],
            'accel': [0, 0, 0],
            'mag': [0, 0, 0]
        }
        
    def log(self, message, level=1):
        if level <= self.debugLevel:
            print(message)


    def on_message(self, ws, message):
        self.log(f"Message received: {message}", 2)
        
        data = json.loads(message)
        sensor_type = data['type']
        values = np.array(data['values'])
        timestamp = data['timestamp']

        if sensor_type == 'android.sensor.gyroscope':
            self.log(f"gyro data: {data}", 3)
            self.latest_sensor_data['gyro'] = values
        elif sensor_type == 'android.sensor.accelerometer':
            self.log(f"accel data: {data}", 3)
            self.latest_sensor_data['accel'] = values
        elif sensor_type == 'android.sensor.magnetic_field':
            self.log(f"mag data: {data}", 3)
            self.latest_sensor_data['mag'] = values
  
        self.latest_sensor_data['timestamp'] = timestamp
            
        self.notify_callbacks(self.latest_sensor_data)


    def notify_callbacks(self, data):
        for callback in self.callbacks:
            callback(data)

    def on_error(self, ws, error):
        self.log(f"WebSocket Error: {error}", 1)

    def on_close(self, ws, close_code, reason):
        self.log(f"WebSocket Closed - Code: {close_code}, Reason: {reason}", 1)

    def on_open(self, ws):
        self.log("WebSocket Connection Opened", 1)

    def connect(self):
        print("Connecting to server:", json.dumps(self.sensors))
        url = f"ws://{self.address}/sensors/connect?types=[{','.join(json.dumps(sensor) for sensor in self.sensors)}]"
        self.ws = websocket.WebSocketApp(url,
                         on_open=self.on_open,
                         on_message=self.on_message,
                         on_error=self.on_error,
                         on_close=self.on_close)
        threading.Thread(target=self.ws.run_forever).start()

    def add_callback(self, callback):
        self.callbacks.append(callback)

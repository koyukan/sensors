import json
import numpy as np
import asyncio
import websockets

class SensorDataHandler:
    def __init__(self, address, sensors, debugLevel=0, notify_synchronously=False):
        self.address = address
        self.sensors = sensors
        self.debugLevel = debugLevel
        self.ws = None
        self.callbacks = []
        self.notify_synchronously = notify_synchronously
        self.latest_sensor_data = {
            'timestamp': None,
            'gyro': None,
            'accel': None,
            'mag': None,
        }

    def log(self, message, level=1):
        if level <= self.debugLevel:
            print(message)

    async def on_message(self, message):
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

        if all(self.latest_sensor_data[key] is not None for key in ['gyro', 'accel', 'mag']):
            await self.notify_callbacks(self.latest_sensor_data)
            if self.notify_synchronously:
                self.latest_sensor_data = {
                    'timestamp': None,
                    'gyro': None,
                    'accel': None,
                    'mag': None,
                }

    async def notify_callbacks(self, data):
        for callback in self.callbacks:
            if asyncio.iscoroutinefunction(callback):
                await callback(data)
            else:
                callback(data)

    async def connect(self):
        url = f"ws://{self.address}/sensors/connect?types=[{','.join(json.dumps(sensor) for sensor in self.sensors)}]"
        async with websockets.connect(url) as ws:
            self.ws = ws
            self.log("WebSocket Connection Opened", 1)
            try:
                async for message in ws:
                    await self.on_message(message)
            except websockets.ConnectionClosedError as e:
                self.log(f"WebSocket Closed - Reason: {str(e)}", 1)

    def add_callback(self, callback):
        self.callbacks.append(callback)

# Usage
# handler = SensorDataHandler('your_address', ['sensor1', 'sensor2'], debugLevel=2)
# asyncio.run(handler.connect())

import asyncio
import websockets
import numpy as np
import json
import math
from ahrsPhoneSensor import SensorDataHandler
from ahrs_Mad import AhrsProcessor
from euler_serial import EulerSerial

class NumpyEncoder(json.JSONEncoder):
    """ Custom encoder for numpy data types """
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)

class SensorDataServer:
    def __init__(self, address, port, data_source="phone"):
        self.data_source = data_source
        self.clients = set()
        self.port = port
        self.ahrs_processor = AhrsProcessor(
            sample_rate=1000, gain=0.041, gyroscope_range=2000,
            acceleration_rejection=10, magnetic_rejection=10, recovery_trigger_period=5*1000
        )

        if self.data_source == "phone":
            self.handler = SensorDataHandler(
                address, 
                ["android.sensor.accelerometer", "android.sensor.gyroscope", "android.sensor.magnetic_field", "android.sensor.orientation"],
                debugLevel=0, notify_synchronously=True
            )
            self.handler.add_callback(self.process_and_broadcast)
        elif self.data_source == "serial":
            self.handler = EulerSerial('/dev/ttyACM1', baud_rate=921600)
            self.handler.set_on_data_handler(self.process_and_broadcast)

    async def process_and_broadcast(self, data):
        # Process data with AHRS algorithm, if the data source is serial, add orientation data to the data dictionary
       # Ensure the data is converted to NumPy arrays
        gyro = np.array(data['gyro'], dtype=float)
        accel = np.array(data['accel'], dtype=float)
        mag = np.array(data['mag'], dtype=float)
        orientation = np.array(data.get('orientation', [0, 0, 0]), dtype=float)  # Default to [0, 0, 0] if not present
        
        #If data source is serial divide the timestamp by 1e6 if it is phone data source then divide by 1e9
        if self.data_source == "serial":
            timestamp = data['timestamp'] / 1e6
        elif self.data_source == "phone":
            timestamp = data['timestamp'] / 1e9

        ahrs_data = self.ahrs_processor.process_sensor_data(
            gyro,
            accel,
            mag,
            orientation,
            timestamp,
        )
        # Use the custom JSON encoder
        message = json.dumps(ahrs_data, cls=NumpyEncoder)
        await self.broadcast(message)

    async def broadcast(self, message):
        # Broadcast message to all connected WebSocket clients
        if self.clients:  # Check if there are any connected clients
            print(f"Broadcasting message: {message}")
            await asyncio.wait([client.send(message) for client in self.clients])

    async def register(self, websocket):
        self.clients.add(websocket)

    async def unregister(self, websocket):
        self.clients.discard(websocket)

    async def websocket_handler(self, websocket, path):
        # Register websocket connection
        await self.register(websocket)
        try:
            await websocket.wait_closed()
        finally:
            await self.unregister(websocket)

    async def main(self):
        # Start the sensor handler connection based on the data source
        if self.data_source == "phone":
            asyncio.create_task(self.handler.connect())
        elif self.data_source == "serial":
            await self.handler.start_reading()

        # Start the WebSocket server
        async with websockets.serve(self.websocket_handler, "localhost", self.port):
            await asyncio.Future()  # Run forever

if __name__ == "__main__":
    # Example usage
    server = SensorDataServer("10.0.0.46:8080", 5678, data_source="phone")  # Change data_source to "phone" if needed
    asyncio.run(server.main())

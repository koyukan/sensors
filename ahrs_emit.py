import asyncio
import websockets
import numpy as np
import json
from ahrsPhoneSensor import SensorDataHandler
from ahrs_Mad import AhrsProcessor


class NumpyEncoder(json.JSONEncoder):
        """ Custom encoder for numpy data types """
        def default(self, obj):
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            return json.JSONEncoder.default(self, obj)

class SensorDataServer:
    def __init__(self, address, port):
        self.handler = SensorDataHandler(address, ["android.sensor.accelerometer", "android.sensor.gyroscope", "android.sensor.magnetic_field"], debugLevel=0, notify_synchronously=True)
        self.handler.add_callback(self.process_and_broadcast)
        self.ahrs_processor = AhrsProcessor(sample_rate=10, gain=0.041, gyroscope_range=2000, acceleration_rejection=100, magnetic_rejection=100, recovery_trigger_period=5*10)
        self.clients = set()
        self.port = port
    
    

    async def process_and_broadcast(self, data):
        # Process data with AHRS algorithm
        ahrs_data = self.ahrs_processor.process_sensor_data(
            gyro=data['gyro'],
            accel=data['accel'],
            mag=data['mag'],
            timestamp=data['timestamp']
        )
        # Use the custom JSON encoder
        message = json.dumps(ahrs_data, cls=NumpyEncoder)
        await self.broadcast(message)

    async def broadcast(self, message):
        # Broadcast message to all connected WebSocket clients
        if self.clients:  # Check if there are any connected clients
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
        # Start the sensor handler connection
        asyncio.create_task(self.handler.connect())
        # Start the WebSocket server
        async with websockets.serve(self.websocket_handler, "localhost", self.port):
            await asyncio.Future()  # Run forever

if __name__ == "__main__":
    server = SensorDataServer("10.0.0.128:8080", 5678)
    asyncio.run(server.main())

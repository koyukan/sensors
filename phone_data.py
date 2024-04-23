import json
import numpy as np
import threading
import websocket
from filters import FIRFilter, RCFilter

class SensorDataHandler:
    def __init__(self, address, sensors, normalize=False, debugLevel=0, filter_configs={}):
        self.address = address
        self.sensors = sensors
        self.normalize = normalize
        self.debugLevel = debugLevel
        self.ws = None
        self.callbacks = []
        self.filters = {sensor: self.create_filters(filter_configs.get(sensor, [])) for sensor in sensors}
        self.latest_sensor_data = {sensor: None for sensor in sensors}

    def log(self, message, level=1):
        if level <= self.debugLevel:
            print(message)

    def create_filters(self, filter_config):
        """ Initialize filters based on the configuration provided """
        filters = []
        for config in filter_config:
            if config['type'] == 'FIR':
                filters.append(FIRFilter(**config['params']))
            elif config['type'] == 'RC':
                filters.append(RCFilter(**config['params']))
        return filters

    def apply_filters(self, sensor_type, values):
        """ Apply configured filters sequentially to the values """
        for filter_obj in self.filters[sensor_type]:
            values = np.array([filter_obj.update(v) for v in values])
        return values

    def on_message(self, ws, message):
        self.log(f"Message received: {message}", 2)
        data = json.loads(message)
        sensor_type = data['type']
        values = np.array(data['values'])
        timestamp = data['timestamp']

        if self.normalize:
            values = self.normalize_values(values)
        if sensor_type in self.filters:
            values = self.apply_filters(sensor_type, values)

        self.latest_sensor_data[sensor_type] = (timestamp, values)
        self.notify_callbacks(sensor_type, timestamp, values)

    def normalize_values(self, values):
        norm = np.linalg.norm(values)
        return values / norm if norm != 0 else values

    def notify_callbacks(self, sensor_type, timestamp, data):
        for callback in self.callbacks:
            callback(sensor_type, timestamp, data)

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

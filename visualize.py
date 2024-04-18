import sys
import websocket
import json
import numpy as np
import pyqtgraph.opengl as gl
from PyQt5 import QtWidgets, QtCore
import pyqtgraph as pg

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
    mx_prime = mx * np.cos(roll_rad) + my * np.sin(pitch_rad) * np.sin(roll_rad) + mz * np.cos(pitch_rad) * np.sin(roll_rad)
    my_prime = my * np.cos(pitch_rad) - mz * np.sin(pitch_rad)
    yaw = np.arctan2(-my_prime, mx_prime)
    return np.degrees(yaw)  # Convert radians to degrees

class WebSocketThread(QtCore.QThread):
    data_received = QtCore.pyqtSignal(str)

    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
        self.ws = websocket.WebSocketApp(self.url,
                                         on_open=self.on_open,
                                         on_message=self.on_message,
                                         on_error=self.on_error,
                                         on_close=self.on_close)
        self.ws.run_forever()

    def on_message(self, ws, message):
        self.data_received.emit(message)

    def on_error(self, ws, error):
        print("Error occurred:", error)

    def on_close(self, ws, close_code, reason):
        print("Connection closed, close code:", close_code, "reason:", reason)

    def on_open(self, ws):
        print("Connected to the server")

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        # Create a GL View widget to display data
        self.gl_widget = gl.GLViewWidget()
        self.setCentralWidget(self.gl_widget)

        # Adjust the view to look from top
        self.gl_widget.setCameraPosition(distance=10, elevation=90, azimuth=0)

        # Create a 3D rectangular prism resembling a phone
        self.cube = gl.GLBoxItem()
        self.cube.setSize(x=1, y=2, z=0.1)  # Phone-like dimensions, where y is length, x is width, and z is thickness
        self.cube.translate(0.5, 1, 0.05)  # Adjust to center the box
        self.gl_widget.addItem(self.cube)

        self.timer = QtCore.QTimer()
        self.timer.setInterval(100)  # Update every 100 ms
        self.timer.timeout.connect(self.update_cube_orientation)
        self.timer.start()

        # WebSocket Thread
        self.thread = WebSocketThread('ws://10.0.0.128:8080/sensors/connect?types=["android.sensor.accelerometer","android.sensor.gyroscope","android.sensor.magnetic_field"]')
        self.thread.data_received.connect(self.handle_data)
        self.thread.start()

    def handle_data(self, message):
        data = json.loads(message)
        sensor_type = data['type']
        values = data['values']
        latest_sensor_data[sensor_type] = values

    def update_cube_orientation(self):
        if all(latest_sensor_data.values()):
            pitch, roll = calculate_pitch_roll(normalize(np.array(latest_sensor_data['android.sensor.accelerometer'])))
            yaw = calculate_yaw(normalize(np.array(latest_sensor_data['android.sensor.magnetic_field'])), pitch, roll)

            # Calculate rotations
            yaw_rad = np.radians(yaw)
            pitch_rad = np.radians(pitch)
            roll_rad = np.radians(roll)

            rot_yaw = np.array([
                [np.cos(yaw_rad), -np.sin(yaw_rad), 0, 0],
                [np.sin(yaw_rad), np.cos(yaw_rad), 0, 0],
                [0, 0, 1, 0],
                [0, 0, 0, 1]
            ])
            rot_pitch = np.array([
                [np.cos(pitch_rad), 0, np.sin(pitch_rad), 0],
                [0, 1, 0, 0],
                [-np.sin(pitch_rad), 0, np.cos(pitch_rad), 0],
                [0, 0, 0, 1]
            ])
            rot_roll = np.array([
                [1, 0, 0, 0],
                [0, np.cos(roll_rad), -np.sin(roll_rad), 0],
                [0, np.sin(roll_rad), np.cos(roll_rad), 0],
                [0, 0, 0, 1]
            ])

            # Multiply rotation matrices
            rotation_matrix = np.linalg.multi_dot([rot_yaw, rot_pitch, rot_roll])

            # Flatten the matrix and correctly pass it to Transform3D
            flattened_matrix = rotation_matrix.flatten()
            transform = pg.Transform3D(*flattened_matrix)  # Unpack the flattened array
            self.cube.setTransform(transform)



if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

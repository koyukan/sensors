import sys
import websocket
import json
import numpy as np
from PyQt5 import QtWidgets, QtCore, QtGui
import pyqtgraph as pg
import pyqtgraph.opengl as gl

def quaternion_to_euler(w, x, y, z):
    # Roll (x-axis rotation)
    sinr_cosp = 2 * (w * x + y * z)
    cosr_cosp = 1 - 2 * (x**2 + y**2)
    roll = np.arctan2(sinr_cosp, cosr_cosp)

    # Pitch (y-axis rotation)
    sinp = 2 * (w * y - z * x)
    if abs(sinp) >= 1:
        pitch = np.sign(sinp) * np.pi / 2  # use 90 degrees if out of range
    else:
        pitch = np.arcsin(sinp)

    # Yaw (z-axis rotation)
    siny_cosp = 2 * (w * z + x * y)
    cosy_cosp = 1 - 2 * (y**2 + z**2)
    yaw = np.arctan2(siny_cosp, cosy_cosp)

    return np.degrees(yaw), np.degrees(pitch), np.degrees(roll)  # Convert radians to degrees


def quaternion_to_rotation_matrix(q):
    # Normalize the quaternion to avoid errors
    q = q / np.linalg.norm(q)
    qw, qx, qy, qz = q

    # Calculate the rotation matrix elements
    return np.array([
        [1 - 2*qy**2 - 2*qz**2,     2*qx*qy - 2*qz*qw,     2*qx*qz + 2*qy*qw],
        [2*qx*qy + 2*qz*qw,         1 - 2*qx**2 - 2*qz**2, 2*qy*qz - 2*qx*qw],
        [2*qx*qz - 2*qy*qw,         2*qy*qz + 2*qx*qw,     1 - 2*qx**2 - 2*qy**2]
    ])


class WebSocketThread(QtCore.QThread):
    data_received = QtCore.pyqtSignal(str)

    def __init__(self, url):
        super(WebSocketThread, self).__init__()
        self.url = url

    def run(self):
        # Create the WebSocket connection
        self.ws = websocket.WebSocketApp(self.url,
                                         on_open=self.on_open,
                                         on_message=self.on_message,
                                         on_error=self.on_error,
                                         on_close=self.on_close)
        self.ws.run_forever()

    def on_open(self, ws):
        print("Connected to the server")

    def on_message(self, ws, message):
        # Parse the JSON message
        data = json.loads(message)
        rotation_vector = data['values']
        q = np.array([rotation_vector[3], rotation_vector[0], rotation_vector[1], rotation_vector[2]])  # Reorder to [w, x, y, z]
        yaw, pitch, roll = quaternion_to_euler(q[0], q[1], q[2], q[3])
        print("Yaw: {:.2f}, Pitch: {:.2f}, Roll: {:.2f}".format(yaw, pitch, roll))
        self.data_received.emit(message)

    def on_error(self, ws, error):
        print("Error occurred:", error)

    def on_close(self, ws, close_code, reason):
        print("Connection closed, close code:", close_code, "reason:", reason)

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        # Setup the main OpenGL widget
        self.gl_widget = gl.GLViewWidget()
        self.setCentralWidget(self.gl_widget)
        self.gl_widget.setCameraPosition(distance=10, elevation=10, azimuth=180)

        # Add grid
        grid = gl.GLGridItem()
        self.gl_widget.addItem(grid)

        # Create and add the 3D cube representing the phone
        self.cube = gl.GLBoxItem()
        self.cube.setSize(x=1, y=2, z=0.1)  # Dimensions of the cube
        self.cube.translate(-0.5, -1, -0.5) 
        self.gl_widget.addItem(self.cube)

        # Setup the WebSocket thread for receiving sensor data
        self.thread = WebSocketThread('ws://10.0.0.128:8080/sensor/connect?type=android.sensor.rotation_vector')
        self.thread.data_received.connect(self.handle_data)
        self.thread.start()

    def handle_data(self, message):
        data = json.loads(message)
        rotation_vector = data['values']
        self.update_cube_orientation(rotation_vector)

    def update_cube_orientation(self, rotation_vector):
        # Assuming rotation_vector is [x, y, z, w] (quaternion)
        q = np.array([rotation_vector[3], rotation_vector[0], rotation_vector[1], rotation_vector[2]])  # Reorder to [w, x, y, z]
        rotation_matrix = quaternion_to_rotation_matrix(q)

        # Extend the 3x3 rotation matrix to a 4x4 matrix
        rotation_matrix_4x4 = np.eye(4)  # Start with an identity matrix
        rotation_matrix_4x4[:3, :3] = rotation_matrix  # Place the 3x3 matrix in the top-left

        # Update transformation considering the cube's geometric center
        transform = QtGui.QMatrix4x4()
        transform.translate(-0.5, -1, -0.5)  # Translate to center the cube
        transform *= QtGui.QMatrix4x4(*rotation_matrix_4x4.flatten())  # Apply rotation
        transform.translate(-0.5, -1, -0.5)  # Translate back

        self.cube.setTransform(transform)



if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

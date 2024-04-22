import sys
import websocket
import json
import numpy as np
from PyQt5 import QtWidgets, QtCore
import pyqtgraph as pg
import pyqtgraph.opengl as gl
from pyqtgraph.opengl import GLMeshItem, GLScatterPlotItem
from filterpy.kalman import ExtendedKalmanFilter
from filterpy.common import Q_discrete_white_noise
import math

# Dictionary to store the latest readings
latest_sensor_data = {
    'android.sensor.accelerometer': None,
    'android.sensor.gyroscope': None,
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

def calculate_laser_intersection(yaw, pitch, roll, p=-2500):
    """ Calculate the intersection of the laser with a plane at z = p. """
    yaw_rad = math.radians(yaw)
    pitch_rad = math.radians(pitch)
    roll_rad = math.radians(roll)
    
    # Rotation matrices
    R_yaw = np.array([
        [math.cos(yaw_rad), -math.sin(yaw_rad), 0],
        [math.sin(yaw_rad), math.cos(yaw_rad), 0],
        [0, 0, 1]
    ])
    R_pitch = np.array([
        [math.cos(pitch_rad), 0, math.sin(pitch_rad)],
        [0, 1, 0],
        [-math.sin(pitch_rad), 0, math.cos(pitch_rad)]
    ])
    R_roll = np.array([
        [1, 0, 0],
        [0, math.cos(roll_rad), -math.sin(roll_rad)],
        [0, math.sin(roll_rad), math.cos(roll_rad)]
    ])
    
    # Apply rotations to a forward-pointing vector
    direction = np.array([0, 0, 1])  # Assuming the laser points forward
    direction = R_yaw @ R_pitch @ R_roll @ direction
    dx, dy, dz = direction
    
    if dz == 0:
        return None  # Prevent division by zero if laser points parallel to the plane
    
    t = p / dz  # Solve for intersection with plane
    x = t * dx
    y = t * dy
    return (x, y)

def setup_ekf():
    ekf = ExtendedKalmanFilter(dim_x=6, dim_z=6)
    ekf.x = np.zeros(6)  # initial state: [yaw, pitch, roll, gyro_x, gyro_y, gyro_z]
    ekf.F = np.eye(6)  # State transition matrix
    ekf.H = np.eye(6)  # Measurement matrix
    ekf.P *= 100  # Initial state covariance, a larger value reflects initial uncertainty

    # Measurement noise covariance matrix (assuming equal uncertainty for all measurements)
    ekf.R = np.eye(6) * 0.5

    # Process noise covariance matrix
    # Define the variances for each of the state variables
    var_yaw = 0.1   # Variance for yaw
    var_pitch = 0.1 # Variance for pitch
    var_roll = 0.1  # Variance for roll
    var_gyro_x = 0.01  # Variance for gyroscopic data on x-axis
    var_gyro_y = 0.01  # Variance for gyroscopic data on y-axis
    var_gyro_z = 0.01  # Variance for gyroscopic data on z-axis

    # Constructing a diagonal covariance matrix directly
    ekf.Q = np.diag([var_yaw, var_pitch, var_roll, var_gyro_x, var_gyro_y, var_gyro_z])

    return ekf

class WebSocketThread(QtCore.QThread):
    data_received = QtCore.pyqtSignal(str)

    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
        self.ws = websocket.WebSocketApp(self.url, on_open=self.on_open, on_message=self.on_message, on_error=self.on_error, on_close=self.on_close)
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
        
        # Setup the Extended Kalman Filter
        self.ekf = setup_ekf()

        # Setup the main OpenGL widget
        self.gl_widget = gl.GLViewWidget()
        self.setCentralWidget(self.gl_widget)
        self.gl_widget.setCameraPosition(distance=10, elevation=10, azimuth=0)

        # Create and add the 3D cube representing the phone
        self.cube = gl.GLBoxItem()
        self.cube.setSize(x=1, y=2, z=0.1)  # Dimensions of the cube
        self.cube.translate(-0.5, -1, -0.5)  # Positioning the cube
        self.gl_widget.addItem(self.cube)

        # Adjust the plane for laser point projection
        plane_z = -2500  # Distance from the origin along the z-axis
        verts = np.array([
            [-5000, -5000, plane_z],
            [5000, -5000, plane_z],
            [5000, 5000, plane_z],
            [-5000, 5000, plane_z]
        ])
        faces = np.array([
            [0, 1, 2],
            [0, 2, 3]
        ])
        self.plane = GLMeshItem(vertexes=verts, faces=faces, color=(0.7, 0.7, 0.7, 0.5), drawEdges=True)
        self.gl_widget.addItem(self.plane)

        # Setup a scatter plot item to represent the laser point
        self.laser_point = GLScatterPlotItem(pos=np.array([[0, 0, plane_z]]), color=(1, 0, 0, 1), size=10)
        self.gl_widget.addItem(self.laser_point)

        # Setup a timer to update the cube orientation
        self.timer = QtCore.QTimer()
        self.timer.setInterval(100)  # Update interval in milliseconds
        self.timer.timeout.connect(self.update_cube_orientation)
        self.timer.start()

        # Setup the WebSocket thread for receiving sensor data
        self.thread = WebSocketThread('ws://10.0.0.128:8080/sensors/connect?types=["android.sensor.accelerometer","android.sensor.gyroscope"]')
        self.thread.data_received.connect(self.handle_data)
        self.thread.start()

    def handle_data(self, message):
        data = json.loads(message)
        sensor_type = data['type']
        values = data['values']
        latest_sensor_data[sensor_type] = values
        self.update_ekf()

    def update_ekf(self):
        if all(latest_sensor_data.values()):
            accel = np.array(latest_sensor_data['android.sensor.accelerometer'])
            gyro = np.array(latest_sensor_data['android.sensor.gyroscope'])

            # Normalize accelerometer data
            accel_normalized = normalize(accel)

            # Calculate pitch and roll from accelerometer
            pitch, roll = calculate_pitch_roll(accel_normalized)
            
            # Assume a placeholder yaw value or another way to compute it
            yaw = 0  # Placeholder, update accordingly
            
            # Prepare the measurement vector z, ensure it matches expected dimension
            z = np.array([yaw, pitch, roll, *gyro])  # Now z should be of length 6

            # Predict the next state
            self.ekf.predict()

            # Update the EKF with the new measurements
            self.ekf.update(z, self.HJacobian_at, self.Hx)

            # Apply the new orientation to the cube
            self.update_cube_orientation()


    @staticmethod
    def HJacobian_at(x):
        """ Return the Jacobian matrix of Hx at x. """
        return np.eye(len(x))  # Identity matrix since measurement directly maps state variables.

    @staticmethod
    def Hx(x):
        """ Measurement function that maps the state vector x to the measurements. """
        return x  # Direct mapping in this simple case.

    def update_cube_orientation(self):
        yaw, pitch, roll = self.ekf.x[:3]
        yaw_rad = np.radians(yaw)
        pitch_rad = np.radians(pitch)
        roll_rad = np.radians(roll)

        laser_pos = calculate_laser_intersection(yaw, pitch, roll, p=-2500)
        if laser_pos:
            self.laser_point.setData(pos=np.array([[laser_pos[0], laser_pos[1], -2500]]))

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
        rotation_matrix = np.linalg.multi_dot([rot_yaw, rot_pitch, rot_roll])
        translate_to_origin = np.array([
            [1, 0, 0, 0.5],
            [0, 1, 0, 1.0],
            [0, 0, 1, 0.05],
            [0, 0, 0, 1]
        ])
        translate_back = np.array([
            [1, 0, 0, -0.5],
            [0, 1, 0, -1.0],
            [0, 0, 1, -0.05],
            [0, 0, 0, 1]
        ])
        full_transformation_matrix = np.dot(translate_to_origin, np.dot(rotation_matrix, translate_back))
        flattened_matrix = full_transformation_matrix.flatten()
        transform = pg.Transform3D(*flattened_matrix)
        self.cube.setTransform(transform)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

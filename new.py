import sys
import numpy as np
from PyQt5 import QtWidgets, QtCore
import pyqtgraph as pg
import pyqtgraph.opengl as gl
from phone_data import SensorDataHandler  # Ensure this module correctly imports FIRFilter and RCFilter

data_store = []

def calculate_pitch_roll(accel):
    ax, ay, az = accel
    pitch = np.arctan2(-ax, np.sqrt(ay**2 + az**2))
    roll = np.arctan2(ay, az)
    return np.degrees(pitch), np.degrees(roll)  # Convert radians to degrees

def sensor_callback(sensor_type, timestamp, data):
    if sensor_type == 'android.sensor.accelerometer':
        pitch, roll = calculate_pitch_roll(data)
        timestamp_sec = timestamp / 1000000  # Convert timestamp to seconds
        data_store.append((timestamp_sec, pitch, roll))

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)


    def create_3d(self):
        # Setup the main OpenGL widget
        self.gl_widget = gl.GLViewWidget()
        self.setCentralWidget(self.gl_widget)
        self.gl_widget.setCameraPosition(distance=10, elevation=10, azimuth=0)

        # Create and add the 3D cube representing the phone
        self.cube = gl.GLBoxItem()
        self.cube.setSize(x=1, y=2, z=0.1)  # Dimensions of the cube
        self.cube.translate(-0.5, -1, -0.5)  # Positioning the cube
        self.gl_widget.addItem(self.cube)
        
    def update_cube_orientation(self, pitch, roll):
        pitch_rad = np.radians(pitch)
        roll_rad = np.radians(roll)

        # Rotation matrix for pitch
        rot_pitch = np.array([
            [np.cos(pitch_rad), 0, np.sin(pitch_rad), 0],
            [0, 1, 0, 0],
            [-np.sin(pitch_rad), 0, np.cos(pitch_rad), 0],
            [0, 0, 0, 1]
        ])
        # Rotation matrix for roll
        rot_roll = np.array([
            [1, 0, 0, 0],
            [0, np.cos(roll_rad), -np.sin(roll_rad), 0],
            [0, np.sin(roll_rad), np.cos(roll_rad), 0],
            [0, 0, 0, 1]
        ])
        # Combine the rotations
        rotation_matrix = np.dot(rot_pitch, rot_roll)

        # Translate to center, apply rotation, and translate back
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
        transform = gl.Transform3D(flattened_matrix)
        self.cube.setTransform(transform)
    
    def create_plot(self):
        self.graphWidget = pg.PlotWidget()
        self.setCentralWidget(self.graphWidget)
        self.graphWidget.setBackground("#fafafa")
        self.graphWidget.setTitle("Orientation Data Plot", color="#8d6e63", size="20pt")

        self.plot_lines = {
            'Pitch': self.graphWidget.plot([], [], pen=pg.mkPen(color="#FF0000"), name='Pitch'),
            'Roll': self.graphWidget.plot([], [], pen=pg.mkPen(color="#00FF00"), name='Roll')
        }

        self.timer = QtCore.QTimer()
        self.timer.setInterval(50)  # Update plot every 50 ms
        self.timer.timeout.connect(self.update_plot_data)
        self.timer.start()

    def update_plot_data(self):
        # Get the latest data points; limit to the last 1000 points for performance
        time_data = [d[0] for d in data_store[-1000:]]
        pitch_data = [d[1] for d in data_store[-1000:]]
        roll_data = [d[2] for d in data_store[-1000:]]

        # Update the plots
        self.plot_lines['Pitch'].setData(time_data, pitch_data)
        self.plot_lines['Roll'].setData(time_data, roll_data)



# Filter configurations
filter_configs = {
    'android.sensor.accelerometer': [
        {'type': 'FIR', 'params': {'length': 10, 'coefficient': 0.1}},
        {'type': 'RC', 'params': {'cutoff_freq_hz': 5, 'sample_time_s': 0.01}}
    ],
    'android.sensor.gyroscope': [
        
        {'type': 'FIR', 'params': {'length': 10, 'coefficient': 0.1}},
        {'type': 'RC', 'params': {'cutoff_freq_hz': 5, 'sample_time_s': 0.01}}
    ]
}

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    # Set up the sensor data handler
    handler = SensorDataHandler(
        "192.168.1.30:8080",
        ["android.sensor.accelerometer", "android.sensor.gyroscope"],
        normalize=False,
        debugLevel=5,
        filter_configs=filter_configs
    )
    handler.add_callback(sensor_callback)
    handler.connect()

    window = MainWindow()
    window.show()
    window.create_plot()
    sys.exit(app.exec_())

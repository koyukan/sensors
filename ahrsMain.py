import sys
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtGui import QQuaternion,QVector4D
import pyqtgraph as pg
import pyqtgraph.opengl as gl
import numpy as np
from ahrs.filters import Madgwick
from ahrsPhoneSensor import SensorDataHandler
from ahrs_colored import ColoredGLBoxItem
from ahrs_Mad import AhrsProcessor


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, handler,algorithm, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.handler = handler
        self.handler.add_callback(self.sensor_callback)
        self.algorithm = algorithm
        self.madgwick_filter = Madgwick(gain_imu=0.01, gain_marg=0.041)
        self.ahrs_processor = AhrsProcessor(sample_rate=10, gain=0.041, gyroscope_range=2000, acceleration_rejection=100, magnetic_rejection=100, recovery_trigger_period=5*10)
        self.setWindowTitle("Sensor Data Visualization")
        self.central_widget = QtWidgets.QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QtWidgets.QVBoxLayout()
        self.central_widget.setLayout(self.layout)
        self.create_3d_view()
        #self.create_plot_view()
        self.create_status_view()
        self.quaternion_store = []
        self.eulerAngles_store = []
        self.sensor_store = []
        self.maxDataPoints = 1000

        # Timer to update the views
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_views)
        self.timer.start(int(1000/65))  # ~65 fps

    def add_quaternion(self, quaternion):
        self.quaternion_store.append(quaternion)
        if len(self.quaternion_store) > self.maxDataPoints:
            self.quaternion_store = self.quaternion_store[-self.maxDataPoints:]

    def add_sensor_data(self, sensor_data):
        self.sensor_store.append(sensor_data)
        if len(self.sensor_store) > self.maxDataPoints:
            self.sensor_store = self.sensor_store[-self.maxDataPoints:]
    
    def add_euler_angles(self, euler_angles):
        self.eulerAngles_store.append(euler_angles)
        if len(self.eulerAngles_store) > self.maxDataPoints:
            self.eulerAngles_store = self.eulerAngles_store[-self.maxDataPoints:]
    
    def update_views(self):
        timestamps = np.array([data[0] for data in self.quaternion_store])
        #quaternions = np.array([data[1] for data in self.quaternion_store])
        # Update the 3D view and the plot view if the data store is not empty
        #if self.quaternion_store :
            #self.update_3d_view(quaternions[-1])
            #self.update_3d_view_euler(self.eulerAngles_store[-1][1])
            # self.update_plot_view(timestamps, quaternions)
        if self.eulerAngles_store:
            self.update_3d_view_euler(self.eulerAngles_store[-1][1])
            #self.update_plot_view(timestamps, np.array([data[1] for data in self.quaternion_store]))


    def sensor_callback(self, data):
    
        '''{'timestamp': 1247359183853915, 'gyro': array([-0.00045379, -0.00443314,  0.00246091]), 'accel': array([-0.03258987,  0.20892762,  9.802446  ]), 'mag': array([ 14.625 ,   5.75  , -39.0625])}'''

        # Store the sensor data
        self.add_sensor_data((data['timestamp'], data))

        #Find the time difference, in seconds, between the current and previous sensor data
        if len(self.sensor_store) > 1:
            time_diff = (self.sensor_store[-1][0] - self.sensor_store[-2][0]) / 1e9
        else:
            time_diff = 0
        
        self.madgwick_filter.Dt = time_diff
        
        
        
        # #Calculate the quaternion
        # quaternion = self.madgwick_filter.updateMARG(
        #     #get the latest quaternion
        #     self.quaternion_store[-1][1] if self.quaternion_store else np.array([1., 0., 0., 0.]),
        #     self.sensor_store[-1][1]['gyro'],
        #     self.sensor_store[-1][1]['accel'],
        #     self.sensor_store[-1][1]['mag'])       


        ahrs_data = self.ahrs_processor.process_sensor_data(
        gyro=self.sensor_store[-1][1]['gyro'],
        accel=self.sensor_store[-1][1]['accel'],
        mag=self.sensor_store[-1][1]['mag'],
        timestamp=data['timestamp']
        )


        # Store the quaternion
        #self.add_quaternion((data['timestamp'],  quaternion))

        # Store the Euler angles
        self.add_euler_angles((data['timestamp'], ahrs_data['euler_angles']))

        self.cube.resetTransform()
        # Apply rotations in sequence: Roll about X, Pitch about Y, Yaw about Z
        self.cube.rotate(ahrs_data['euler_angles'][0], 1.0, 0.0, 0.0)  # Roll
        self.cube.rotate(ahrs_data['euler_angles'][1], 0.0, 1.0, 0.0)  # Pitch
        self.cube.rotate(ahrs_data['euler_angles'][2], 0.0, 0.0, 1.0)  # Yaw




        internal_states = ahrs_data['internal_states']
        flags = ahrs_data['flags']
        for key, label in self.labels.items():
            if key in internal_states:
                label.setText(str(internal_states[key]))
            elif key in flags:
                label.setText(str(flags[key]))
        

   


    def update_3d_view(self, quaternion):
        self.cube.resetTransform()
        q = QQuaternion(QVector4D(quaternion[1], quaternion[2], quaternion[3], quaternion[0]))
        qn = q.normalized()
        axis, angle = qn.getAxisAndAngle()
        self.cube.rotate(angle, axis.x(), axis.y(), axis.z())
        self.gl_widget.update()

    def update_3d_view_euler(self, euler_angles):

        self.gl_widget.update()


    def update_plot_view(self, timestamps, quaternions):
        self.curveQ0.setData(timestamps, quaternions[:, 0])
        self.curveQ1.setData(timestamps, quaternions[:, 1])
        self.curveQ2.setData(timestamps, quaternions[:, 2])
        self.curveQ3.setData(timestamps, quaternions[:, 3])

    def create_3d_view(self):
        self.gl_widget = gl.GLViewWidget()
        self.layout.addWidget(self.gl_widget, 2)  # Give it a stretch factor
        self.gl_widget.setCameraPosition(distance=10, elevation=10, azimuth=0)
        size = [1, 2, 0.2]
        self.cube = ColoredGLBoxItem(size=size)
        self.cube.translate(-0.5, -1, -0.05)
        self.gl_widget.addItem(self.cube)

    def create_plot_view(self):
        self.graphWidget = pg.PlotWidget()
        self.layout.addWidget(self.graphWidget, 1)  # Give it a stretch factor
        self.graphWidget.setBackground("#fafafa")
        self.graphWidget.setTitle("Orientation Data Plot", color="#8d6e63", size="20pt")
        self.curveQ0 = self.graphWidget.plot(pen='r')
        self.curveQ1 = self.graphWidget.plot(pen='g')
        self.curveQ2 = self.graphWidget.plot(pen='b')
        self.curveQ3 = self.graphWidget.plot(pen='y')

    def create_status_view(self):
        self.statusGroup = QtWidgets.QGroupBox("AHRS Status")
        self.layout.addWidget(self.statusGroup)
        statusLayout = QtWidgets.QGridLayout()
        self.statusGroup.setLayout(statusLayout)

        self.labels = {
            'acceleration_error': QtWidgets.QLabel("0"),
            'accelerometer_ignored': QtWidgets.QLabel("False"),
            'acceleration_recovery_trigger': QtWidgets.QLabel("0"),
            'magnetic_error': QtWidgets.QLabel("0"),
            'magnetometer_ignored': QtWidgets.QLabel("False"),
            'magnetic_recovery_trigger': QtWidgets.QLabel("0"),
            'initialising': QtWidgets.QLabel("False"),
            'angular_rate_recovery': QtWidgets.QLabel("False"),
            'acceleration_recovery': QtWidgets.QLabel("False"),
            'magnetic_recovery': QtWidgets.QLabel("False")
        }

        # Add labels to the grid
        statusLayout.addWidget(QtWidgets.QLabel("Acceleration Error:"), 0, 0)
        statusLayout.addWidget(self.labels['acceleration_error'], 0, 1)
        statusLayout.addWidget(QtWidgets.QLabel("Accelerometer Ignored:"), 1, 0)
        statusLayout.addWidget(self.labels['accelerometer_ignored'], 1, 1)
        statusLayout.addWidget(QtWidgets.QLabel("Acceleration Recovery Trigger:"), 2, 0)
        statusLayout.addWidget(self.labels['acceleration_recovery_trigger'], 2, 1)
        statusLayout.addWidget(QtWidgets.QLabel("Magnetic Error:"), 3, 0)
        statusLayout.addWidget(self.labels['magnetic_error'], 3, 1)
        statusLayout.addWidget(QtWidgets.QLabel("Magnetometer Ignored:"), 4, 0)
        statusLayout.addWidget(self.labels['magnetometer_ignored'], 4, 1)
        statusLayout.addWidget(QtWidgets.QLabel("Magnetic Recovery Trigger:"), 5, 0)
        statusLayout.addWidget(self.labels['magnetic_recovery_trigger'], 5, 1)
        statusLayout.addWidget(QtWidgets.QLabel("Initialising:"), 6, 0)
        statusLayout.addWidget(self.labels['initialising'], 6, 1)
        statusLayout.addWidget(QtWidgets.QLabel("Angular Rate Recovery:"), 7, 0)
        statusLayout.addWidget(self.labels['angular_rate_recovery'], 7, 1)
        statusLayout.addWidget(QtWidgets.QLabel("Acceleration Recovery:"), 8, 0)
        statusLayout.addWidget(self.labels['acceleration_recovery'], 8, 1)
        statusLayout.addWidget(QtWidgets.QLabel("Magnetic Recovery:"), 9, 0)
        statusLayout.addWidget(self.labels['magnetic_recovery'], 9, 1)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    handler = SensorDataHandler("10.0.0.128:8080", ["android.sensor.accelerometer", "android.sensor.gyroscope", "android.sensor.magnetic_field"], debugLevel=0, notify_synchronously=True)
    window = MainWindow(handler, algorithm='AHRS')
    window.show()
    handler.connect()
    sys.exit(app.exec_())

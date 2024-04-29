import sys
from PyQt5 import QtWidgets, QtCore
import pyqtgraph as pg
import pyqtgraph.opengl as gl
import numpy as np
from ahrs.filters import Madgwick
from ahrsPhoneSensor import SensorDataHandler


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, handler, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.handler = handler
        self.handler.add_callback(self.sensor_callback)
        self.madgwick_filter = Madgwick()
        self.setWindowTitle("Sensor Data Visualization")
        self.central_widget = QtWidgets.QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QtWidgets.QVBoxLayout()
        self.central_widget.setLayout(self.layout)
        self.create_3d_view()
        self.create_plot_view()
        self.data_store = []
        self.sensor_store = []
        self.maxDataPoints = 1000

        # Timer to update the views
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_views)
        self.timer.start(100)

    def update_views(self):
        timestamps = np.array([data[0] for data in self.data_store])
        quaternions = np.array([data[1] for data in self.data_store])
        # Update the 3D view and the plot view if the data store is not empty
        if len(self.data_store) > 2:
            self.update_3d_view(quaternions[-1])
            self.update_plot_view(timestamps, quaternions)


    def sensor_callback(self, data):
    
        '''{'timestamp': 1247359183853915, 'gyro': array([-0.00045379, -0.00443314,  0.00246091]), 'accel': array([-0.03258987,  0.20892762,  9.802446  ]), 'mag': array([ 14.625 ,   5.75  , -39.0625])}'''

        # Store the sensor data
        self.sensor_store.append((data['timestamp'], data))

        # Trim the data store
        if len(self.sensor_store) > self.maxDataPoints:
            self.sensor_store = self.sensor_store[-self.maxDataPoints:]

        # Calculate the quaternion
        quaternion = self.madgwick_filter.updateMARG(
            #get the latest quaternion
            self.data_store[-1][1] if self.data_store else np.array([1., 0., 0., 0.]),
            self.sensor_store[-1][1]['gyro'],
            self.sensor_store[-1][1]['accel'],
            self.sensor_store[-1][1]['mag']
        )       

        # Store the quaternion
        self.data_store.append((data['timestamp'], quaternion))

        # Trim the data store
        if len(self.data_store) > self.maxDataPoints:
            self.data_store = self.data_store[-self.maxDataPoints:]





    def update_3d_view(self, quaternion):
        self.cube.resetTransform()
        self.cube.rotate(angle=np.rad2deg(np.arccos(quaternion[0]) * 2), x=quaternion[1], y=quaternion[2], z=quaternion[3])
        self.gl_widget.update()

    def update_plot_view(self, timestamps, quaternions):
        self.curveQ0.setData(timestamps, quaternions[:, 0])
        self.curveQ1.setData(timestamps, quaternions[:, 1])
        self.curveQ2.setData(timestamps, quaternions[:, 2])
        self.curveQ3.setData(timestamps, quaternions[:, 3])

    def create_3d_view(self):
        self.gl_widget = gl.GLViewWidget()
        self.layout.addWidget(self.gl_widget, 1)  # Give it a stretch factor
        self.gl_widget.setCameraPosition(distance=10, elevation=10, azimuth=0)
        self.cube = gl.GLBoxItem()
        self.cube.setSize(x=1, y=2, z=0.1)
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


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    handler = SensorDataHandler("10.0.0.128:8080", ["android.sensor.accelerometer", "android.sensor.gyroscope", "android.sensor.magnetic_field"], debugLevel=0)
    window = MainWindow(handler)
    window.show()
    handler.connect()
    sys.exit(app.exec_())

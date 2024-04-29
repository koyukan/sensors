import sys
import numpy as np
from PyQt5 import QtWidgets, QtCore
import pyqtgraph as pg
import pyqtgraph.opengl as gl
from ahrsPhoneSensor import SensorDataHandler


data_store = []


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.handler = handler
        self.handler.add_callback(self.sensor_callback)


    def sensor_callback(self, sensor_type, timestamp, data):
        # Print the sensortype, timestamp, and data
        print(sensor_type, timestamp, data)

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
        
    
    def create_plot(self):
        self.graphWidget = pg.PlotWidget()
        self.setCentralWidget(self.graphWidget)
        self.graphWidget.setBackground("#fafafa")
        self.graphWidget.setTitle("Orientation Data Plot", color="#8d6e63", size="20pt")


        self.timer = QtCore.QTimer()
        self.timer.setInterval(50)  # Update plot every 50 ms
        self.timer.timeout.connect(self.update_plot_data)
        self.timer.start()

    def update_plot_data(self):
        # Get the latest data points; limit to the last 1000 points for performance
        data = np.array(data_store[-1000:])
        if len(data) == 0:
            return
        

        # Update the plots



# Filter configurations


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    # Set up the sensor data handler
    handler = SensorDataHandler(
        "10.0.0.128:8080",
        ["android.sensor.accelerometer", "android.sensor.gyroscope", "android.sensor.magnetic_field"],
        debugLevel=5,
    )
    

    window = MainWindow()
    window.handler = handler
    window.handler.connect()
    window.show()
    window.create_plot()
    sys.exit(app.exec_())

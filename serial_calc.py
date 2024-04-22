# Import the EulerSerial class
from euler_serial import EulerSerial
import sys
import time
import numpy as np
from PyQt5 import QtWidgets, QtCore, QtGui
import pyqtgraph as pg
import pyqtgraph.opengl as gl
import math
import matplotlib.pyplot as plt

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        # Set up the plot widget
        data_color = "#d32f2f"   # red
        background_color = "#fafafa" # white (material)
        self.graphWidget = pg.PlotWidget()
        self.setCentralWidget(self.graphWidget)

        self.graphWidget.setBackground(background_color)

        self.graphWidget.setTitle(" Plot", color="#8d6e63", size="20pt")
        
        # Add Axis Labels
        styles = {"color": "#f00", "font-size": "15px"}
        self.graphWidget.setLabel("left", "x", **styles)
        self.graphWidget.setLabel("bottom", "z", **styles)
        self.graphWidget.addLegend()

        self.x_data_line =  self.graphWidget.plot([],[], name="x", pen=pg.mkPen(color=data_color))

        plot_scale = 100
        #Limit the plot axis to -1000 to 1000
        #self.graphWidget.setXRange(-plot_scale, plot_scale)
        #self.graphWidget.setYRange(-plot_scale, plot_scale)
        # Auto-scale the plot with a padding of 0.1
        self.graphWidget.enableAutoRange('xy', True)

        # Add padding to the plot
        self.graphWidget.plotItem.getViewBox().setAspectLocked(True)

    
        
        #shared data
        self.x_data = []
       
        self.z_data = []

        self.timer = QtCore.QTimer()
        self.timer.setInterval(50)
        self.timer.timeout.connect(self.update_plot_data) # call update_plot_data function every 50 milisec
        self.timer.start()
        # Add a laser point item
        # self.laser_point_item = gl.GLScatterPlotItem(pos=np.array([[-0.5, -0.5, -2500]]), size=10, color=(1, 0, 0, 1))
        #Add a laser line item
        self.laser_point_item = gl.GLLinePlotItem(pos=np.array([[1,0, 0], [1, 0, -2500]]), color=(1, 0, 0, 1))
        #self.gl_widget.addItem(self.laser_point_item)

    
    def update_plot_data(self):
        
        # limit lists data to 1000 items 
        limit = -100 
        
        #Get max value of x and z data
        max_x = max(self.x_data)
        max_z = max(self.z_data)
        #Get min value of x and z data
        min_x = min(self.x_data)
        min_z = min(self.z_data)

        # Update the data.
        self.x_data_line.setData(self.x_data[limit:], self.z_data[limit:])  
        self.graphWidget.setXRange(min_x -5 , max_x +5)
        self.graphWidget.setYRange(min_z  -5 , max_z +5)
        
    def handle_data(self,message):
        data = list(map(float, message.split()))
        roll, pitch, yaw = data[:3]
       
         #Get epoch time in miliseconds for the data
        epoch_time = float(time.time())
        #rotation rate degrees per second
        yaw_rot_rate = 0.4

        ##yaw -= yaw_rot_rate * (epoch_time)

        # use the relative vector function to get the intersection point and plot it
        x, z = relative_vector(0, -2, -2, math.radians(yaw),math.radians(roll),math.radians(pitch),200)

       
        # limit lists data to 1000 items 
        self.x_data.append(x)
        self.z_data.append(z)

        

    def calculate_laser_intersection(self, yaw, pitch, roll):
        # Convert degrees to radians
        yaw_rad = math.radians(yaw)
        pitch_rad = math.radians(pitch)
        roll_rad = math.radians(roll)

        # Define the transformation for rotations using NumPy arrays
        R_yaw = np.array([
            [np.cos(yaw_rad), -np.sin(yaw_rad), 0],
            [np.sin(yaw_rad), np.cos(yaw_rad), 0],
            [0, 0, 1]
        ])
        R_pitch = np.array([
            [np.cos(pitch_rad), 0, np.sin(pitch_rad)],
            [0, 1, 0],
            [-np.sin(pitch_rad), 0, np.cos(pitch_rad)]
        ])
        R_roll = np.array([
            [1, 0, 0],
            [0, np.cos(roll_rad), -np.sin(roll_rad)],
            [0, np.sin(roll_rad), np.cos(roll_rad)]
        ])

        direction = np.array([0, 1, 0])  # Initial direction vector pointing upwards from the cube
        
        direction = R_yaw @ R_pitch @ R_roll @ direction

        dz = direction[2]
        if dz == 0:
            return None  # Prevent division by zero

        t = (-2500 - (-0.5)) / dz  # Calculate intersection with a distant plane at z = -2500
        x = 0.5 + t * direction[0]
        y = 1 + t * direction[1]

        return (x, y, -2500)  # Return the 3D coordinates of the intersection point


# Function to create a rotation matrix about the z-axis
def rotation_matrix_z(theta):
    return np.array([
        [np.cos(theta), -np.sin(theta), 0],
        [np.sin(theta), np.cos(theta), 0],
        [0, 0, 1]
    ])

# Function to create a rotation matrix about the y-axis
def rotation_matrix_y(phi):
    return np.array([
        [np.cos(phi), 0, np.sin(phi)],
        [0, 1, 0],
        [-np.sin(phi), 0, np.cos(phi)]
    ])

# Function to create a rotation matrix about the x-axis
def rotation_matrix_x(gamma):
    return np.array([
        [1, 0, 0],
        [0, np.cos(gamma), -np.sin(gamma)],
        [0, np.sin(gamma), np.cos(gamma)]
    ])

# Function to rotate a point by given angles theta, phi, gamma
def rotate_point(x, y, z, theta, phi, gamma):
    point = np.array([x, y, z])
    Rz = rotation_matrix_z(theta)
    Ry = rotation_matrix_y(phi)
    Rx = rotation_matrix_x(gamma)
    # Combine the rotations
    # R = np.dot(Rz, np.dot(Ry, Rx))
    new_point = Rz @ Ry @ Rx @ point
    # Apply the rotation to the point
    

    return new_point

# Example usage
theta = np.radians(0)  # Convert degrees to radians
phi = np.radians(0)
gamma = np.radians(90)
x, y, z = 0, 1, 0  # Coordinates of the point to be rotated

x1,y1,z1 = rotate_point(0, 0, 1, theta, phi, gamma)
x2, y2, z2 = rotate_point(0, -1, 1, theta, phi, gamma)

new_coordinates = rotate_point(x, y, z, theta, phi, gamma)

print("New coordinates:", new_coordinates)


def project_line_on_plane(x1, y1, z1, x2, y2, z2, p):
    # Check if the line is parallel to the plane
    if y2 - y1 == 0:
        if y1 == p:
            print("The line is on the plane.")
        else:
            print("The line is parallel to the plane and does not intersect it.")
        return None
    
    # Calculate the parameter t where the line intersects the plane y = p
    t = (p - y1) / (y2 - y1)
    
    # Calculate the x and z coordinates at the intersection
    x = x1 + t * (x2 - x1)
    z = z1 + t * (z2 - z1)
    
    # Return the coordinates of the intersection point on the plane y = p
    return (x, z)





# Define function that gives a vector relative to anotehr vector in 3D
def relative_vector(xd, yd, zd, yaw, roll, pitch ,p ):
    x1 = -xd 
    x2= - xd
    y1 = -yd-1
    y2 = -yd
    z1 = -zd
    z2 = -zd


   # print ("0:" , x1, y1, z1)
    x1, y1, z1 = rotate_point(x1, y1, z1, yaw, roll, pitch)
    #print ("1:" , x1, y1, z1)
    x2, y2, z2 = rotate_point(x2, y2, z2, yaw, roll, pitch)
    #print ("2:" , x2, y2, z2)
    x3, z3 = project_line_on_plane(x1, y1, z1, x2, y2, z2, p)
    #print ("3:" , x3, z3)


    return x3, z3


if __name__ == "__main__":

    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
        # Create an instance of EulerSerial
    euler_reader = EulerSerial('/dev/ttyACM0', baud_rate=921600)
    # Start reading
    euler_reader.start_reading()
    euler_reader.set_on_data_handler(window.handle_data)

    try:
        # Keep the main thread running, otherwise Python will exit
        input("Press enter to stop...\n")
    except KeyboardInterrupt:
        # If user interrupts the program (e.g., by pressing Ctrl+C), stop reading and close the port
        euler_reader.stop_reading()
        euler_reader.close()
        print("Stopped reading and closed the serial port.")
        sys.exit(app.exec_())

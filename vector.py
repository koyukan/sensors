import sys
import websocket
import json
import numpy as np
from PyQt5 import QtWidgets, QtCore, QtGui
import pyqtgraph as pg
import pyqtgraph.opengl as gl
import math
import matplotlib.pyplot as plt

plt.switch_backend('TkAgg')

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



def get_relative_vector(box, xd, yd, zd):
    """
    Computes a new vector relative to the box's current position, based on the provided offsets.
    
    Parameters:
        box: An object that has a transformation matrix and methods for manipulating it.
        xd (float): The x-offset from the box's current position.
        yd (float): The y-offset from the box's current position.
        zd (float): The z-offset from the box's current position.

    Returns:
        A QVector3D representing the new vector's coordinates.
    """
    # Create a new QMatrix4x4 object for translation
    translation = QtGui.QMatrix4x4()
    translation.translate(xd, yd, zd)

    # Apply this translation to the box's current transformation
    new_transform = box.transform() * translation

    # Assuming the origin is the reference point, transform this point to the new coordinates
    new_vector = new_transform.map(QtGui.QVector3D(0, 0, 0))

    return new_vector


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
        # print("Yaw: {:.2f}, Pitch: {:.2f}, Roll: {:.2f}".format(yaw, pitch, roll))
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
        self.fig, self.ax = plt.subplots()

        # Create and add the 3D cube representing the phone
        self.cube = gl.GLBoxItem()
        self.cube.setSize(x=1, y=2, z=0.1)  # Dimensions of the cube
        #self.cube.translate(-0.5, -1, -0.5) 
        self.gl_widget.addItem(self.cube)

        # Create a line relative to the cube
        relative_vector = get_relative_vector(self.cube, 0, 10, 0)
        relative_vector_np = np.array([relative_vector.x(), relative_vector.y(), relative_vector.z()])

        # Now use it in GLLinePlotItem
        self.line = gl.GLLinePlotItem(pos=np.array([relative_vector_np]), color=(1, 0, 0, 1),)
        
        self.gl_widget.addItem(self.line)



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

        #Limit the plot axis to -1000 to 1000
        self.graphWidget.setXRange(-10, 10)
        self.graphWidget.setYRange(-10, 10)
        
        
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

        # Setup the WebSocket thread for receiving sensor data
        self.thread = WebSocketThread('ws://10.0.0.128:8080/sensor/connect?type=android.sensor.rotation_vector')
        self.thread.data_received.connect(self.handle_data)
        self.thread.start()
    
    def update_plot_data(self):
        
        # limit lists data to 1000 items 
        limit = -100 

        # Update the data.
        self.x_data_line.setData(self.x_data[limit:], self.z_data[limit:])  
        
    def handle_data(self, message):
        data = json.loads(message)
        rotation_vector = data['values']
        q = np.array([rotation_vector[3], rotation_vector[0], rotation_vector[1], rotation_vector[2]])  # Reorder to [w, x, y, z]
        yaw, pitch, roll = quaternion_to_euler(q[0], q[1], q[2], q[3])
        # self.update_cube_orientation(rotation_vector)
        # self.updateRelativeVector(5, 100, 0)
        # Create a figure and axis
        


        # use the relative vector function to get the intersection point and plot it
        x, z = relative_vector(0, -2, -2, math.radians(yaw),math.radians(roll),math.radians(pitch),20)
        print(x,z)

                # limit lists data to 1000 items 
        self.x_data.append(x)
        self.z_data.append(z)

        



    def updateRelativeVector(self, xd, yd, zd):
        relative_vector = get_relative_vector(self.cube, xd, yd, zd)
        relative_vector_np = np.array([relative_vector.x(), relative_vector.y(), relative_vector.z()])
        self.line.setData(pos=np.array([relative_vector_np, [10, 10, 10]]))

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

    def update_cube_orientation(self, rotation_vector):
        # Assuming rotation_vector is [x, y, z, w] (quaternion)
        q = np.array([rotation_vector[3], rotation_vector[0], rotation_vector[1], rotation_vector[2]])  # Reorder to [w, x, y, z]
        rotation_matrix = quaternion_to_rotation_matrix(q)

        # Extend the 3x3 rotation matrix to a 4x4 matrix
        rotation_matrix_4x4 = np.eye(4)  # Start with an identity matrix
        rotation_matrix_4x4[:3, :3] = rotation_matrix  # Place the 3x3 matrix in the top-left

        # Update transformation considering the cube's geometric center
        transform = QtGui.QMatrix4x4()
        #transform.translate(-0.5, -1, -0.5)  # Translate to center the cube
        transform *= QtGui.QMatrix4x4(*rotation_matrix_4x4.flatten())  # Apply rotation
        

        yaw, pitch, roll = quaternion_to_euler(q[0], q[1], q[2], q[3])
        laser_point = self.calculate_laser_intersection(yaw, pitch, roll)
        if laser_point:
            self.laser_point_item.setData(pos=np.array([[1, 0, 0], laser_point]), color=(1, 0, 0, 1))
            
           # self.laser_point_item.setData(pos=[laser_point + np.array([0.5, 1, 0.5])])
            

        self.cube.setTransform(transform)


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
    sys.exit(app.exec_())
    

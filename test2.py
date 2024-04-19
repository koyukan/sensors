import numpy as np
# Create a plot from the relative vector and the origin
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import math

# Ensure correct display backend
plt.switch_backend('TkAgg')

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


    print ("0:" , x1, y1, z1)
    x1, y1, z1 = rotate_point(x1, y1, z1, yaw, roll, pitch)
    print ("1:" , x1, y1, z1)
    x2, y2, z2 = rotate_point(x2, y2, z2, yaw, roll, pitch)
    print ("2:" , x2, y2, z2)
    x3, z3 = project_line_on_plane(x1, y1, z1, x2, y2, z2, p)
    print ("3:" , x3, z3)


    return x3, z3





# Create a figure and axis
fig, ax = plt.subplots()


# use the relative vector function to get the intersection point and plot it
x, z = relative_vector(0, -2, -2, math.radians(45),0,0,30)
print(x,z)

ax.plot(x, z, 'ro')

# show the plot
plt.show()
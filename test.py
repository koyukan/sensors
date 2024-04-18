import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import math

# Ensure correct display backend
plt.switch_backend('TkAgg')

def calculate_laser_intersection(yaw, pitch):
    yaw_rad = math.radians(yaw)
    pitch_rad = math.radians(pitch)
    
    dx = math.cos(pitch_rad) * math.sin(yaw_rad)
    dy = math.cos(pitch_rad) * math.cos(yaw_rad)
    dz = -math.sin(pitch_rad)
    
    if dz == 0:
        return None
    
    t = -2500 / dz
    x = t * dx
    y = t * dy
    return (x, y)

# Global list to accumulate laser points
laser_points = []

def animate(i):
    point = calculate_laser_intersection(data['yaw'][i], data['pitch'][i])
    if point is not None:
        laser_points.append(point)
        
        # Update plot limits dynamically based on new point
        x_min, x_max = ax.get_xlim()
        y_min, y_max = ax.get_ylim()
        x_lim = (min(x_min, point[0]), max(x_max, point[0]))
        y_lim = (min(y_min, point[1]), max(y_max, point[1]))
        ax.set_xlim(x_lim)
        ax.set_ylim(y_lim)
        
        line.set_data(zip(*laser_points))  # Unpack list of tuples to separate lists
    return line,

# Load data from CSV
data = pd.read_csv('angles.csv')

# Initialize plot with initial limits (can be adjusted if needed)
fig, ax = plt.subplots()
ax.set_xlim(-10, 10)  # Initial x-axis limits (adjust based on expected data range)
ax.set_ylim(-10, 10)  # Initial y-axis limits (adjust based on expected data range)
line, = ax.plot([], [], 'ro-', markersize=2)

# Create animation with adjusted interval for smoother animation
ani = FuncAnimation(fig, animate, frames=len(data), interval=285.7, blit=False, repeat=False)

plt.show()

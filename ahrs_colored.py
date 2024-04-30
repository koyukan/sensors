from pyqtgraph.opengl import GLMeshItem
import numpy as np

class ColoredGLBoxItem(GLMeshItem):
    def __init__(self, size=(1, 1, 1), color=None, **kwds):
        super(ColoredGLBoxItem, self).__init__(**kwds)
        self.size = size
        self.color = color if color is not None else [
            (1, 0, 0, 1),  # Red
            (0, 1, 0, 1),  # Green
            (0, 0, 1, 1),  # Blue
            (1, 1, 0, 1),  # Yellow
            (0, 1, 1, 1),  # Cyan
            (1, 0, 1, 1)   # Magenta
        ]
        self.setData()

    def setData(self):
        verts, faces, colors = self.generateMeshData(self.size, self.color)
        self.setMeshData(vertexes=verts, faces=faces, vertexColors=colors, faceColors=colors)

    def generateMeshData(self, size, color):
        x, y, z = size
        verts = np.array([
            [0, 0, 0],
            [x, 0, 0],
            [0, y, 0],
            [x, y, 0],
            [0, 0, z],
            [x, 0, z],
            [0, y, z],
            [x, y, z]
        ])
        # Define the faces (triangles) for each face of the box
        faces = np.array([
            [0, 1, 2], [1, 3, 2],  # Bottom
            [4, 5, 6], [5, 7, 6],  # Top
            [0, 1, 4], [1, 5, 4],  # Front
            [2, 3, 6], [3, 7, 6],  # Back
            [0, 2, 4], [2, 6, 4],  # Left
            [1, 3, 5], [3, 7, 5]   # Right
        ])
        colors = np.array([color[f // 2 % len(color)] for f in range(12)])  # Assign colors to triangles
        return verts, faces, colors

# Usage within your main application should remain the same, but ensure size is passed correctly:
# cube = ColoredGLBoxItem(size=(1, 2, 0.1))

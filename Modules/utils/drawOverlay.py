
import numpy as np

def ellipses(x_centers, y_centers, minor_axis_lengths, major_axis_lengths, orientations, l1, l2):
    # Draw ellipses with minor and major axis. There is no build-in function for ellipses in PyQtGraph, so we draw them using the plotCurveItems.

    axesX = []
    axesY = []
    axesConnect = []
    ellipsesX = []
    ellipsesY = []
    ellipsesConnect = []
    phi = np.linspace(0, 2*np.pi, 25)
    for x0, y0, a, b, theta in zip(x_centers, y_centers, minor_axis_lengths, major_axis_lengths, orientations):
        # Ellipse
        x = 0.5*a*np.cos(phi)
        y = 0.5*b*np.sin(phi)
        ellipsesX.extend(x0 +  x*np.sin(theta) - y*np.cos(theta))
        ellipsesY.extend(y0 +  x*np.cos(theta) + y*np.sin(theta))
        connect = np.ones(phi.size)
        connect[-1] = 0 # Replace last element with 0
        ellipsesConnect.extend(connect)
        # Axes
        x1 = np.cos(theta)*0.5*b
        y1 = np.sin(theta)*0.5*b
        x2 = -np.sin(theta)*0.5*a
        y2 = np.cos(theta)*0.5*a
        axesX.extend([x0, x0 + x1, x0 + x2, x0])
        axesY.extend([y0, y0 - y1, y0 - y2, y0])
        axesConnect.extend([1, 0, 1, 0])
	   
    l1.setData(x=axesX, y=axesY, connect=np.array(axesConnect)) 
    l2.setData(x=ellipsesX, y=ellipsesY, connect=np.array(ellipsesConnect))


def circles(x_centers, y_centers, radii, l1):
    # Draw circles with given radii.

    circlesX = []
    circlesY = []
    circlesConnect = []
    phi = np.linspace(0, 2*np.pi, 25)
    for x0, y0, r in zip(x_centers, y_centers, radii):
        # Circle
        x = r*np.cos(phi)
        y = r*np.sin(phi)
        circlesX.extend(x0 +  x)
        circlesY.extend(y0 +  y)
        connect = np.ones(phi.size)
        connect[-1] = 0 # replace last element with 0
        circlesConnect.extend(connect)

    l1.setData(x=circlesX, y=circlesY, connect=np.array(circlesConnect))
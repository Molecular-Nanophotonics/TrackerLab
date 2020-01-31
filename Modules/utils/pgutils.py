
import numpy as np
from PyQt5 import QtCore, QtGui
import pyqtgraph as pg

class LineItem(pg.GraphicsObject):
    def __init__(self, p1, p2, color, width=1):
        pg.GraphicsObject.__init__(self)
        self.p1 = p1
        self.p2 = p2
        self.color = color
        self.width = width
        self.generatePicture()

    def generatePicture(self):
        self.picture = QtGui.QPicture()
        p = QtGui.QPainter(self.picture)
        p.setPen(pg.mkPen(self.color, width=self.width))
        p.drawLine(QtCore.QPointF(self.p1[0], self.p1[1]), QtCore.QPointF(self.p2[0], self.p2[1]))
        p.end()

    def paint(self, p, *args):
        p.drawPicture(0, 0, self.picture)

    def boundingRect(self):
        return QtCore.QRectF(self.picture.boundingRect())


class CircleItem(pg.GraphicsObject):
    def __init__(self, center, radius, color='r', width=1):
        pg.GraphicsObject.__init__(self)
        self.center = center
        self.radius = radius
        self.color = color
        self.width = width
        self.generatePicture()

    def generatePicture(self):
        self.picture = QtGui.QPicture()
        p = QtGui.QPainter(self.picture)
        p.setPen(pg.mkPen(self.color, width=self.width))
        p.drawEllipse(QtCore.QPointF(self.center[0],  self.center[1]), self.radius, self.radius)
        p.end()

    def paint(self, p, *args):
        p.drawPicture(0, 0, self.picture)

    def boundingRect(self):
        return QtCore.QRectF(self.picture.boundingRect())
    
 
class EllipseItem(pg.GraphicsObject):
    def __init__(self, center, major_axis_length, minor_axis_length, theta, color='r', width=1):
        pg.GraphicsObject.__init__(self)
        self.center = center
        self.major_axis_length = major_axis_length
        self.minor_axis_length = minor_axis_length
        self.theta = theta
        self.color = color
        self.width = width
        self.generatePicture()

    def generatePicture(self):
        self.picture = QtGui.QPicture()
        p = QtGui.QPainter(self.picture)
        p.setPen(pg.mkPen(self.color, width=self.width))
        p.save()
        p.translate(self.center[0], self.center[1])
        p.rotate(self.theta)
        p.translate(-self.center[0], -self.center[1])
        p.drawEllipse(QtCore.QPointF(self.center[0],  self.center[1]), 0.5*self.major_axis_length, 0.5*self.minor_axis_length)
        p.restore()
        p.end()

    def paint(self, p, *args):
        p.drawPicture(0, 0, self.picture)

    def boundingRect(self):
        return QtCore.QRectF(self.picture.boundingRect())
    
    
class RectangleItem(pg.GraphicsObject):
    def __init__(self, topLeft, size, color='r', width=1):
        pg.GraphicsObject.__init__(self)
        self.topLeft = topLeft
        self.size = size
        self.color = color
        self.width = width
        self.generatePicture()

    def generatePicture(self):
        self.picture = QtGui.QPicture()
        p = QtGui.QPainter(self.picture)
        p.setPen(pg.mkPen(self.color, width=self.width))
        topLeft = QtCore.QPointF(self.topLeft[0], self.topLeft[1])
        size = QtCore.QSizeF(self.size[0], self.size[1])
        p.drawRect(QtCore.QRectF(topLeft, size))
        p.end()

    def paint(self, p, *args):
        p.drawPicture(0, 0, self.picture)

    def boundingRect(self):
        return QtCore.QRectF(self.picture.boundingRect())
    
    

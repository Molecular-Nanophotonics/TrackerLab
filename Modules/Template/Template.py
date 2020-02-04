# -*- coding: utf-8 -*-
"""
Discription: Template module with detailed comments.
Author(s):   M. Fränzl
Data:        28/01/20
"""

import numpy as np

from skimage.feature import blob_dog
import pandas as pd

import os
from PyQt5.uic import loadUi
from PyQt5.QtCore import pyqtSignal
from PyQt5 import QtWidgets
import pyqtgraph as pg

from .utils import drawOverlay, ini


class Module(QtWidgets.QWidget):

    updated = pyqtSignal()
        
    def __init__(self):
        super().__init__(None)
        
        moduleName = os.path.splitext(os.path.basename(__file__))[0] # The module name is defined by the nam of this file 
        loadUi('Modules/' + moduleName + '.ui', self) # Load the *.ui file with the same filename
        self.iniFile = 'Modules/' + moduleName + '.ini' # Define the filename for the *.ini file 
        
        # Connect the input widgets events to the "updated" event of the module. The widget names are defined in the *.ui file.
        self.thresholdSpinBox.valueChanged.connect(self.updated.emit)
        self.maxSigmaSpinBox.valueChanged.connect(self.updated.emit)
        
    # The attach function is called when the module is selected in the main application
    def attach(self, plot):
        self.p = plot # Get reference to the plot
        self.pc = pg.PlotCurveItem(pen=pg.mkPen('r', width=3), brush=pg.mkBrush(None), pxMode=False) # Create plot item for the overlay.
        self.p.addItem(self.pc) # Add the plot item to the plot  
        ini.loadSettings(self.iniFile, self.widget) # Restore stettings from the *.ini file
        
    # The detach function is called when the module is deselected in the main application  
    def detach(self):
        self.p.removeItem(self.pc) # Remove the overlay
        ini.saveSettings(self.iniFile, self.widget) # Save stettings to the *.ini file 
       
    # This function is responsible of the actual feature detection.
    # It requires the frame number and an ImageItem as input parameters and needs to return a Pandas DataFrame
    def findFeatures(self, frame, imageItem):
        
        # Get values from the input widgets
        threshold = self.thresholdSpinBox.value()
        maxSigma = self.maxSigmaSpinBox.value()

        # Get the image array from the ImageItem
        image = imageItem.image
        # Detected features in the image. Here we use the Difference of Gaussian (DoG) algorithm provided with the "skimage" package.
        mlist = blob_dog(image/image.max(), max_sigma=maxSigma, threshold=threshold/100)
        radii = mlist[:, 2]*np.sqrt(2)
    
        # Save the detected features as Pandas DataFrame
        features = pd.DataFrame()
        x, y = np.meshgrid(np.arange(0, image.shape[0], 1), np.arange(0, image.shape[1], 1))
        if mlist.size > 0:
            for j in range(mlist.shape[0]):
                mask = (((x - mlist[j, 1])**2 + (y - mlist[j, 0])**2) < (mlist[j, 2]*np.sqrt(2))**2).astype(int)
                features = features.append([{'y': mlist[j, 0],
                                             'x': mlist[j, 1],
                                             'max_intensity': image[mask==1].max(),
                                             'area': 2*np.pi*mlist[j, 2]**2,
                                             'frame': frame,}])
        
        # Set the output image as image of the ImageItem (Here, the output image is the same as the input image)
        imageItem.setImage(image)
        
        # Draw the overlay
        if features.size > 0:
            drawOverlay.circles(features.x.values, features.y.values, radii, self.pc) # Draw circles around the detected features 
            self.numberOfFeatures.setText(str(features.shape[0])) # Display the number of features in a text box
        else:
            self.pc.setData() # Remove overlay
            self.numberOfFeatures.setText('0') # Set the displayed number of features to 0
            
        # Return the features DataDrame
        return features
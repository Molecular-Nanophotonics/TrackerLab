# -*- coding: utf-8 -*-
"""
Discription: Module for Connected-Component Labeling similar to the 
            "Particle Analysis.vi" in the LabVIEW Vision Development Module. Extened to fid the orientation of ellipsoidal Janus Particles.
Author(s):   M. Fränzl, Nicola Söker
Date:        21/01/23
"""

import numpy as np

import skimage
import pandas as pd

import os

from PyQt5.uic import loadUi
from PyQt5.QtCore import pyqtSignal
from PyQt5 import QtWidgets

import pyqtgraph as pg

from ..Utils import pgutils
from ..Utils.settings import saveSettings, restoreSettings


class Module(QtWidgets.QWidget):

    updated = pyqtSignal()
        
    def __init__(self):
        super().__init__(None)
        
        loadUi(os.path.splitext(os.path.relpath(__file__))[0] + '.ui', self)
        self.settingsFile = os.path.splitext(os.path.relpath(__file__))[0] + '.ini'
        
        self.thresholdSpinBox.valueChanged.connect(self.updated.emit)  
        self.minAreaSpinBox.valueChanged.connect(self.updated.emit)  
        self.maxAreaSpinBox.valueChanged.connect(self.updated.emit)
        self.invertCheckBox.stateChanged.connect(self.updated.emit)
        self.maxFeaturesSpinBox.valueChanged.connect(self.updated.emit)
        self.showOverlayCheckBox.stateChanged.connect(self.updated.emit)
        self.flip_x_paramterDoubleSpinBox.valueChanged.connect(self.updated.emit)  
           
    def attach(self, plot):
        self.p = plot
        self.items = []
        restoreSettings(self.settingsFile, self.widget)
        
        
    def detach(self):
        for item in self.items:
            self.p.removeItem(item)
            del item
        saveSettings(self.settingsFile, self.widget)
        

    def findFeatures(self, frame, imageItem):
            
        threshold = self.thresholdSpinBox.value()
        min_area = self.minAreaSpinBox.value()
        max_area = self.maxAreaSpinBox.value()
        max_features = self.maxFeaturesSpinBox.value()
        invert = self.invertCheckBox.checkState()
        flip_x_paramter = self.flip_x_paramterDoubleSpinBox.value()

        features = pd.DataFrame()           
        intensityImage = imageItem.image
        thresholdImage = (intensityImage > threshold).astype(int) # Threshold image
        if invert:
            thresholdImage = 1 - thresholdImage
        labelImage = skimage.measure.label(thresholdImage)
        regions = skimage.measure.regionprops(label_image = labelImage, intensity_image = intensityImage) # http://scikit-image.org/docs/dev/api/skimage.measure.html
        j = 0
        for region in regions:
            # Area filter first 
            if region.area < min_area or region.area > max_area:  # Do not add feature
                continue
            if j >= max_features: # Do not add feature
                continue 
            x_com = region.local_centroid[1]
            y_com = region.local_centroid[0]
            intensity_image = region.intensity_image
            orientation = -region.orientation # the minus sign here is necassary for x = cos(phi) and y = sin(phi) to be true
            L = region.major_axis_length

            min_row, min_col, max_row, max_col = region.bbox
            w = max_col - min_col
            h = max_row - min_row

            x_list = np.linspace(0,w-1,w) - x_com
            y_list = np.linspace(0,h-1,h) - y_com

            x_matrix, y_matrix = np.meshgrid(x_list, y_list)

            x_matrix_particle_frame = x_matrix*np.cos(-orientation + np.pi/2) - y_matrix*np.sin(-orientation + np.pi/2)
            y_matrix_particle_frame = x_matrix*np.sin(-orientation + np.pi/2) + y_matrix*np.cos(-orientation + np.pi/2)
            
            weight_matrix = np.cos( x_matrix_particle_frame / (L/4) ) + flip_x_paramter
            weight_matrix[y_matrix_particle_frame < 0] = - weight_matrix[y_matrix_particle_frame < 0]

            direction_measure = np.mean( weight_matrix*intensity_image, axis = (0, 1) )

            features = features.append([{'y': region.centroid[0], 
                                         'x': region.centroid[1],
                                         'y_weighted': region.weighted_centroid[0],
                                         'x_weighted': region.weighted_centroid[1],
                                         'orientation': -region.orientation,  # the minus sign here is necassary for x = cos(phi) and y = sin(phi) to be true
                                         'minor_axis_length': region.minor_axis_length,
                                         'major_axis_length': region.major_axis_length,
                                         'eccentricity': region.eccentricity,
                                         'area': region.area,
                                         'equivalent_diameter': region.equivalent_diameter,
                                         'filled_area': region.filled_area,
                                         'max_intensity': region.max_intensity,
                                         'mean_intensity': region.mean_intensity,
                                         'direction_measure': direction_measure,
                                         'weights_matrix': weight_matrix,
                                         'x_matrix_particle_frame': x_matrix_particle_frame,
                                         'y_matrix_particle_frame': y_matrix_particle_frame,
                                         'x_matrix': x_matrix,
                                         'y_matrix': y_matrix,
                                         'intensity_matrix': intensity_image,
                                         'h_image': h,
                                         'w_image': w,
                                         'x_com': x_com,
                                         'y_com': y_com,
                                         #'bbox': region.bbox,
                                         'frame': frame,}])
            j += 1 # Feature added
        features.reset_index(drop=True, inplace = True)
        
        imageItem.setImage(thresholdImage)
        
        # Overlay
        for item in self.items:
            self.p.removeItem(item)
            del item
        self.items = []
        if self.showOverlayCheckBox.checkState():
            for i, f in features.iterrows():
                x0 = f.x + 0.5
                y0 = f.y + 0.5
                self.items.append(pgutils.EllipseItem([x0, y0], f.major_axis_length, f.minor_axis_length, np.degrees(f.orientation + np.pi/2), color='r', width=2))
                self.p.addItem(self.items[-1])
                self.items.append(pgutils.LineItem([x0, y0], [x0 + 0.5*f.minor_axis_length*np.cos(f.orientation), y0 + 0.5*f.minor_axis_length*np.sin(f.orientation)], color='b', width=2))
                self.p.addItem(self.items[-1])
                self.items.append(pgutils.LineItem([x0, y0], [x0 - 0.5*f.major_axis_length*np.sin(f.orientation), y0 + 0.5*f.major_axis_length*np.cos(f.orientation)], color='b', width=2))
                self.p.addItem(self.items[-1])

                self.items.append(pgutils.LineItem([x0, y0], [ x0 + np.sign(f.direction_measure)*0.5*f.minor_axis_length*np.cos(f.orientation), y0 + np.sign(f.direction_measure)* 0.5*f.minor_axis_length*np.sin(f.orientation)], color='r', width=1))
                self.p.addItem(self.items[-1])

        if features.size > 0:
            self.numberOfFeatures.setText(str(features.shape[0]))
        else:
            self.numberOfFeatures.setText('0')
        
        return features

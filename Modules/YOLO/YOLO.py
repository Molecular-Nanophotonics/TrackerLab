# -*- coding: utf-8 -*-
"""
Discription: Module for Connected-Component Labeling. 
Author(s):   M. Fränzl
Date:        18/09/18
"""

import numpy as np

from skimage.transform import resize
import pandas as pd

import os

from PyQt5.uic import loadUi
from PyQt5.QtCore import pyqtSignal
from PyQt5 import QtWidgets
import pyqtgraph as pg

try:
	import tensorflow as tf
except:
	print('Error Importing TensorFlow.')
	
import configparser
            
from ..Utils import pgutils
from ..Utils.settings import saveSettings, restoreSettings

from .utils import decode_output

class Module(QtWidgets.QWidget):

    updated = pyqtSignal()
        
    def __init__(self):
        super().__init__(None)
        
        loadUi(os.path.splitext(os.path.relpath(__file__))[0] + '.ui', self)
        self.settingsFile = os.path.splitext(os.path.relpath(__file__))[0] + '.ini'
        
        self.enabled = False
        self.objThresholdSpinBox.setEnabled(False)
        self.nmsThresholdSpinBox.setEnabled(False)
        self.color_list = ['c', 'y', 'm', 'g', 'b']
        
        self.openFileDialogButton.clicked.connect(self.openFileDialog)
        self.objThresholdSpinBox.valueChanged.connect(self.updated.emit)
        self.nmsThresholdSpinBox.valueChanged.connect(self.updated.emit)
        self.showOverlayCheckBox.stateChanged.connect(self.updated.emit)

        
    def openFileDialog(self):
        options = QtWidgets.QFileDialog.DontUseNativeDialog 
        
        file, _ = QtWidgets.QFileDialog.getOpenFileNames(self, 'Load YOLO Model...',  os.path.dirname(os.path.realpath(__file__)) + '/Models', 'Protocol Buffer File (*.pb)', 'Protocol Buffer File (*.pb)', options=options) # 'All Files (*)'
        
        if file:
            self.loadModel(file[0])


    def loadModel(self, modelPath):
        
        pbFile = modelPath
        
        # Import graph from *.pb file
        gf = tf.gfile.FastGFile(pbFile, 'rb')
        graph_def = tf.GraphDef()
        graph_def.ParseFromString(gf.read()) # Parses a serialized binary message into the current message.
        gf.close()
        
        # Import information specific to YOLO from *.ini file
        iniFile = os.path.splitext(pbFile)[0] + '.ini'   
        config = configparser.ConfigParser()
        config.read(iniFile)   
        section = config.sections()[0]
        self.IMAGE_H = int(config[section]['IMAGE_H'])
        self.IMAGE_W = int(config[section]['IMAGE_W'])
        self.LABELS  = config[section]['LABELS'].split(',')
        self.CLASSES = len(self.LABELS)
        self.ANCHORS = [float(a) for a in config[section]['ANCHORS'].split(',')]
        self.INPUT_NODE_NAME  = config[section]['INPUT_NODE_NAME']
        self.OUTPUT_NODE_NAME = config[section]['OUTPUT_NODE_NAME']
   
        # Start TensorFlow session and import graph
        self.session = tf.Session()
        self.session.graph.as_default()
        tf.import_graph_def(graph_def)
        self.output_tensor = self.session.graph.get_tensor_by_name('import/' + self.OUTPUT_NODE_NAME + ':0')
        
        # If no error ... 
        self.lineEdit.setText(pbFile)   
        self.enabled = True
        self.objThresholdSpinBox.setEnabled(True)
        self.nmsThresholdSpinBox.setEnabled(True)
        self.updated.emit()    
        
        
    def attach(self, plot):
        self.p = plot
        self.items = []
        self.enabled = False
        self.objThresholdSpinBox.setEnabled(False)
        self.nmsThresholdSpinBox.setEnabled(False)
        restoreSettings(self.settingsFile, self.widget)
        self.numberOfFeatures.setText('0')
        #if os.path.isfile(self.lineEdit.text()):
        #    self.loadModel(self.lineEdit.text())
        #else:
        self.lineEdit.setText('')
        
    
    def detach(self):
        for item in self.items:
            self.p.removeItem(item) 
        saveSettings(self.settingsFile, self.widget)
       

    def findFeatures(self, frame, imageItem):
        
        #threshold = self.thresholdSpinBox.value()
        #maxSigma = self.maxSigmaSpinBox.value()
        OBJ_THRESHOLD = self.objThresholdSpinBox.value()
        NMS_THRESHOLD = self.nmsThresholdSpinBox.value()
        
        image = imageItem.image
        dimx = image.shape[1]
        dimy = image.shape[0]
        
        features = pd.DataFrame()
        if self.enabled:
            image = resize(image, (416, 416))
            input_tensor = np.expand_dims(np.stack((image, image, image)/image.max(), axis=-1), 0) # reshape image to input tensor shape
            output = self.session.run(self.output_tensor, {'import/' + self.INPUT_NODE_NAME + ':0': input_tensor}) # run model
            bboxes = decode_output(output[0], self.ANCHORS, self.CLASSES, OBJ_THRESHOLD, NMS_THRESHOLD) # decode output tensor
            
            for bbox in bboxes:
                xmin = bbox.xmin*dimx
                ymin = bbox.ymin*dimy
                xmax = bbox.xmax*dimx
                ymax = bbox.ymax*dimy
                class_idx = bbox.get_label()
                features = features.append([{'x': 0.5*(xmin + xmax),
                                             'y': 0.5*(ymin + ymax),
                                             'xmin': xmin, 
                                             'ymin': ymin,
                                             'xmax': xmax,
                                             'ymax': ymax,
                                             'w': xmax - xmin,
                                             'h': ymax - ymin,
                                             'class_idx': class_idx,
                                             'frame': frame,}])
    
            for item in self.items:
                self.p.removeItem(item) 
            self.items = []
            if self.showOverlayCheckBox.checkState():
                for i, f in features.iterrows():
                    item = pgutils.RectangleItem([f.xmin, f.ymin], [f.w, f.h], self.color_list[int(f.class_idx)], width=2)
                    self.items.append(item)
                    self.p.addItem(item)   
        
            #imageItem.setImage(image)
        
            if features.size > 0:
                self.numberOfFeatures.setText(str(features.shape[0]))
            else:
                self.pc.setData()
                self.numberOfFeatures.setText('0')
            

        return features

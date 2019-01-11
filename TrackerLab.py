# -*- coding: utf-8 -*-
"""
Discription: This is the Molecular Nanophotonics TrackLab.
Author(s): M. Fränzl
Data: 18/09/18
"""

import sys
from PyQt5 import QtWidgets
from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import QMainWindow, QWidget, QApplication, QDialog, QMessageBox

from PyQt5.uic import loadUi

import pyqtgraph as pg
import pyqtgraph.exporters

from pyqtgraph import QtCore, QtGui
#import inspect

from matplotlib import cm # for colormaps

import numpy as np

import pandas as pd
import skimage
from skimage import io
from skimage import morphology      
from skimage.util import invert

from scipy import ndimage
import os, fnmatch, glob

from nptdms import TdmsFile

import subprocess as sp # for calling ffmpeg

import Modules

import platform

class SettingsWindow(QDialog):
    def __init__(self):
        super().__init__(None,  QtCore.Qt.WindowCloseButtonHint)
        
        loadUi('SettingsWindow.ui', self)
        
        self.okButton.clicked.connect(self.accept)
        self.cancelButton.clicked.connect(self.reject)

        

class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.ui = loadUi('TrackerLab.ui', self)

        self.displayedIcon = QtGui.QIcon(QtGui.QPixmap("Resources/Circle.png")) 
        ## draw the icon  
        #pixmap = QtGui.QPixmap(32, 32)
        #pixmap.fill(QtCore.Qt.white)
        #painter = QtGui.QPainter(pixmap)
        #painter.setBrush(QtCore.Qt.black)
        #painter.drawEllipse(QtCore.QPoint(16, 16), 5, 5)
        #self.displayedIcon = QtGui.QIcon(pixmap)
        
        # restore setting from TrackerLab.ini file
        self.restoreSettings() 
        
        self.selectFilesButton.clicked.connect(self.selectFilesDialog)
        self.addFilesButton.clicked.connect(self.addFilesDialog)
        self.removeFilesButton.clicked.connect(self.removeFiles)
        
        self.fileList = []
        self.fileListWidget.itemDoubleClicked.connect(self.fileDoubleClicked)
        self.exposure = []
        
        self.frameSlider.valueChanged.connect(self.frameSliderChanged)   
        self.frameSpinBox.valueChanged.connect(self.frameSpinBoxChanged)  
        #self.fileComboBox.currentIndexChanged.connect(self.fileComboBoxChanged) 
      
        self.colormapComboBox.currentIndexChanged.connect(self.colormapComboBoxChanged) 
        self.scalingComboBox.currentIndexChanged.connect(self.scalingComboBoxChanged) 
        
        self.lminSlider.valueChanged.connect(self.lminSliderChanged)   
        self.lminSpinBox.valueChanged.connect(self.lminSpinBoxChanged)  
        self.lmaxSlider.valueChanged.connect(self.lmaxSliderChanged)   
        self.lmaxSpinBox.valueChanged.connect(self.lmaxSpinBoxChanged)  
        
        self.batchButton.clicked.connect(self.batchButtonClicked)
 
        self.medianCheckBox.stateChanged.connect(self.update)  
        self.subtractMeanCheckBox.stateChanged.connect(self.update)  
        self.medianSpinBox.valueChanged.connect(self.update)
        self.maskCheckBox.stateChanged.connect(self.update)
        self.maskXSpinBox.valueChanged.connect(self.maskChanged)
        self.maskYSpinBox.valueChanged.connect(self.maskChanged)
        self.maskRadiusSpinBox.valueChanged.connect(self.maskChanged)
        self.maskComboBox.currentIndexChanged.connect(self.maskChanged) 
        self.mask = np.array([])
        
        self.trackingCheckBox.stateChanged.connect(self.trackingCheckBoxChanged)
        self.tabWidget.currentChanged.connect(self.update) 
        self.tabIndex = 0
        
        self.exportTypeComboBox.currentIndexChanged.connect(self.exportTypeComboBoxChanged) 

        # Connect all valueChange and stateChange events in the tabWidget to update()      
        for tabIndex in range(self.tabWidget.count()):
            tab = self.tabWidget.widget(tabIndex);
            for obj in tab.findChildren(QtGui.QWidget):
                if obj.metaObject().className() == 'QSpinBox':
                    obj.valueChanged.connect(self.update)  
                if obj.metaObject().className() == 'QCheckBox':
                    obj.stateChanged.connect(self.update) 
                    
        
        self.actionOpen.triggered.connect(self.selectFilesDialog)
        self.actionExit.triggered.connect(self.close)
        self.actionSettings.triggered.connect(self.showSettingsWindow)
        self.actionAbout.triggered.connect(self.aboutClicked)

        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 0.75)
        pg.setConfigOption('imageAxisOrder', 'row-major')
        
        graphicsLayout = pg.GraphicsLayoutWidget()
        self.layout.addWidget(graphicsLayout)
        
        '''
        self.p = graphicsLayout.addPlot()
        self.p.setAspectLocked(True)
        self.img = pg.ImageItem()
        self.p.addItem(self.img)
        '''
        
        self.p1 = graphicsLayout.addPlot(row=1, col=1)
        self.p1.showAxis('top')
        self.p1.showAxis('right')
        self.p1.getAxis('top').setStyle(showValues=False)
        self.p1.getAxis('right').setStyle(showValues=False)
        self.p1.getAxis('top').setHeight(10)
        self.p1.getAxis('right').setWidth(15)
        #self.p1.setLimits(xMin=0, yMin=0)
        self.p1.setAspectLocked(True) 
        self.im1 = pg.ImageItem()
        self.p1.addItem(self.im1)
        self.p1.getViewBox().invertY(True)
        
        self.p2 = graphicsLayout.addPlot(row=1, col=2)
        self.p2.showAxis('top')
        self.p2.showAxis('right')
        self.p2.getAxis('top').setStyle(showValues=False)
        self.p2.getAxis('right').setStyle(showValues=False)
        self.p2.getAxis('top').setHeight(10)
        self.p2.getAxis('right').setWidth(15)
        #self.p2.setLimits(xMin=0, yMin=0)
        self.p2.setAspectLocked(True)
        self.im2 = pg.ImageItem()
        self.p2.addItem(self.im2)
        self.p2.getViewBox().invertY(True)
    
        self.p2.setXLink(self.p1.vb)
        self.p2.setYLink(self.p1.vb)

        self.exportButton.clicked.connect(self.exportButtonClicked)

        # items for overlay
        #self.sp1 = pg.ScatterPlotItem(pen=pg.mkPen('r', width=3), brush=pg.mkBrush(None), pxMode=False)
        #self.p2.addItem(self.sp1)
        
        self.lp1 = pg.PlotCurveItem(pen=pg.mkPen('b', width=3), brush=pg.mkBrush(None), pxMode=False)  
        self.p2.addItem(self.lp1)

        self.lp2 = pg.PlotCurveItem(pen=pg.mkPen('r', width=3), brush=pg.mkBrush(None), pxMode=False)
        self.p2.addItem(self.lp2)
                
        #self.p = pg.PlotItem(pen=pg.mkPen('r', width=2), brush=pg.mkBrush(None), pxMode=False)
        #self.p2.addItem(self.p)
        

        # mouse moved events                
        self.p1.scene().sigMouseMoved.connect(self.mouseMoved)   
        self.p2.getViewBox().scene().sigMouseMoved.connect(self.mouseMoved) 

        
        self.batch = False
        self.spots = pd.DataFrame()
        
        self.statusBar.showMessage('Ready')
        self.progressBar = QtGui.QProgressBar()
        self.statusBar.addPermanentWidget(self.progressBar)
        self.cancelButton = QtGui.QPushButton("Cancel")
        self.cancelButton.setEnabled(False)
        self.canceled = False
        self.cancelButton.clicked.connect(self.cancelClicked)   
        self.statusBar.addPermanentWidget(self.cancelButton)
        self.cancelButton.setStyleSheet("width:91; height:23; margin-right: 5px;");

        self.progressBar.setMinimumHeight(15)
        self.progressBar.setMaximumHeight(15)
        self.progressBar.setMinimumWidth(250)
        self.progressBar.setMaximumWidth(250)
        self.progressBar.setValue(0)
        
        # load colormaps        
        self.colormaps = []
        self.colormapComboBox.clear()
        for file in glob.glob('Colormaps/*.csv'):
            self.colormapComboBox.addItem(os.path.splitext(os.path.basename(file))[0])
            self.colormaps.append(np.loadtxt(file, delimiter=','))
               
        if not self.colormaps:
            self.colormapComboBox.addItem('Gray') # default
        else:
            self.colormapComboBox.setCurrentIndex(self.colormapComboBox.findText('Gray'))
          
        #pg.SignalProxy(self.p.scene().sigMouseMoved, rateLimit=60, slot=self.mouseMoved)
        #pg.SignalProxy(self.p2.scene().sigMouseMoved, rateLimit=60, slot=self.mouseMoved)
        
        self.settingsWindow = SettingsWindow() 
        self.settingsWindow.radioButtonHDF5.setChecked(self.hdf5)
        self.settingsWindow.radioButtonCSV.setChecked(self.csv)
        
        # check if FFmpeg is available
        self.ffmpeg = True
        try:
            sp.call(['FFmpeg/ffmpeg'])
        except OSError as e:
            if e.errno == os.errno.ENOENT:
                self.ffmpeg = False # FFmpeg is not installed
                print('FFmpeg is Not Installed. Video Export is Disabled.')
                
        
    def mouseMoved(self, e):
        if self.p1.vb.sceneBoundingRect().contains(e):
            mousePoint = self.p1.vb.mapSceneToView(e)
            x = int(mousePoint.x())
            y = int(mousePoint.y()) 
            if x > 0 and x < self.dimx and y > 0 and y < self.dimy:
                self.infoLabel.setText("x = %d\ty = %d\t[%d]" % (x, y, self.images[self.frameSlider.value(), y ,x]))
                
        if self.p2.vb.sceneBoundingRect().contains(e):
            mousePoint = self.p2.vb.mapSceneToView(e)  
            x = int(mousePoint.x())
            y = int(mousePoint.y()) 
            if x > 0 and x < self.dimx and y > 0 and y < self.dimy:
                self.infoLabel.setText("x = %d\ty = %d\t[%d]" % (x, y, self.processedImage[y, x]))
                
            #vLine.setPos(mousePoint.x())
            #hLine.setPos(mousePoint.y())
    
        
    def update(self):
            
        if self.tabIndex != self.tabWidget.currentIndex():
            self.lp1.clear()
            self.lp2.clear()
            self.tabIndex = self.tabWidget.currentIndex()
        
        self.tab1Threshold = self.tab1ThresholdSpinBox.value()
        self.tab1MinArea = self.tab1MinAreaSpinBox.value()
        self.tab1MaxArea = self.tab1MaxAreaSpinBox.value()
        self.tab1MaxFeatures = self.tab1MaxFeaturesSpinBox.value()
        
        self.tab2Threshold = self.tab2ThresholdSpinBox.value()
        self.tab2MaxSigma = self.tab2MaxSigmaSpinBox.value()
        
        
        if self.scalingComboBox.currentIndex() == 0:
            self.im1.setImage(self.images[self.frameSlider.value()])
        else:
            self.im1.setImage(self.images[self.frameSlider.value()], levels=[self.lminSlider.value(), self.lmaxSlider.value()])             
        
        self.processedImage = self.images[self.frameSlider.value()]
        
        # Image Pre-Processing 
        if self.subtractMeanCheckBox.checkState():
            self.processedImage = self.processedImage -np.mean(self.images,axis=(0))
            self.processedImage[self.processedImage<0] = 0
        
        if self.medianCheckBox.checkState():
            self.processedImage = ndimage.median_filter(self.processedImage, self.medianSpinBox.value())
            
        if self.maskCheckBox.checkState():
            if (self.mask.shape[0] != self.dimy or self.mask.shape[1] != self.dimx):
                self.maskChanged()
            self.processedImage = self.mask*self.processedImage
            

        skimage.io.imsave('image.tif',self.processedImage)
        
        # Tracking
        spots = pd.DataFrame()
        if self.trackingCheckBox.checkState():
            spots = self.findSpots(self.frameSlider.value())   

            self.im2.setImage(self.processedImage) 
            
            if spots.size > 0:
                self.numberOfSpots.setText(str(spots.shape[0]))
            else:
                self.numberOfSpots.setText('0')
                self.lp1.clear()
                self.lp2.clear()
        else:
            self.tabWidget.setEnabled(False)
            if self.scalingComboBox.currentIndex() == 0:
                self.im2.setImage(self.processedImage)
            else:
                self.im2.setImage(self.processedImage, levels=[self.lminSlider.value(), self.lmaxSlider.value()])
            self.lp1.clear()
            self.lp2.clear()
        
        if self.batch:
            self.spots = self.spots.append(spots)
            
        #self.sp.setData(x=spots.x.tolist(), y=spots.y.tolist(), size=10)
        
     # Maximum Tracking     
    def findSpots(self, i):
        
        spots = pd.DataFrame()
        
        args = {}
        for obj in self.tabWidget.currentWidget().findChildren(QtGui.QWidget):
            if obj.metaObject().className() == 'QSpinBox':
                args[obj.objectName()] = obj.value();
            if obj.metaObject().className() == 'QCheckBox':
                args[obj.objectName()] = obj.checkState();     

        method = getattr(Modules, self.tabWidget.currentWidget().objectName())
        spots, self.processedImage  = method(i, self.processedImage, self.lp1, self.lp2, **args)
       
        #Overlay
        #sp.setData(x=features.x.tolist(), y=features.y.tolist(), size=2*np.sqrt(np.array(features.area.tolist())/np.pi))
                                                        
        return spots  


    def maskChanged(self):
        x0 = self.maskXSpinBox.value() #int(self.dimx/2)
        y0 = self.maskYSpinBox.value() #int(self.dimy/2)
        diameter = 2*self.maskRadiusSpinBox.value()
        a = self.maskRadiusSpinBox.value()
        xx, yy= np.meshgrid(np.arange(0, self.dimx, 1), np.arange(0, self.dimy, 1))
        if self.maskComboBox.currentIndex() == 0:
            self.mask = (((xx - x0)**2 + (yy - y0)**2) < (diameter/2)**2).astype(int)
        else:
            self.mask = ((np.abs(xx - x0) < a) & (np.abs(yy - y0) < a)).astype(int)
        self.update()
        
       
    def frameSliderChanged(self, value):
        self.frameSpinBox.setValue(value)
        self.update()
        
    def frameSpinBoxChanged(self, value):
        self.frameSlider.setValue(value)

        
    def colormapComboBoxChanged(self, value):
        if self.colormaps:
            self.im1.setLookupTable(self.colormaps[value])
            if not self.trackingCheckBox.checkState():
                self.im2.setLookupTable(self.colormaps[value])    
        
    def scalingComboBoxChanged(self, value):
        if self.scalingComboBox.isEnabled():
            if self.scalingComboBox.currentIndex() == 0:
                self.enableLevels(False)
            else:
                self.enableLevels(True)
            self.update()
            
        
    def lminSliderChanged(self, value):
        self.lminSpinBox.setValue(value)
        self.im1.setLevels([self.lminSlider.value(), self.lmaxSlider.value()])
        if not self.trackingCheckBox.checkState():
            self.im2.setLevels([self.lminSlider.value(), self.lmaxSlider.value()])
        
    def lminSpinBoxChanged(self, value):
        self.lminSlider.setValue(value)
        
    def lmaxSliderChanged(self, value):
        self.lmaxSpinBox.setValue(value)
        self.im1.setLevels([self.lminSlider.value(), self.lmaxSlider.value()])
        if not self.trackingCheckBox.checkState():
            self.im2.setLevels([self.lminSlider.value(), self.lmaxSlider.value()])
        
    def lmaxSpinBoxChanged(self, value):
        self.lmaxSlider.setValue(value)
        

    def selectFilesDialog(self):
        if platform.system() == 'Darwin': # On MacOS the native file browser sometimes crashes
            options = QtWidgets.QFileDialog.DontUseNativeDialog
        else:
            options = QtWidgets.QFileDialog.Option()
            
        self.files, _ =  QtWidgets.QFileDialog.getOpenFileNames(self, 'Select Files...', self.dir, 'TDMS Files (*.tdms);;TIFF Files (*.tif)', options=options) # 'All Files (*)'
        if self.files:
            self.fileList = []
            self.fileListWidget.clear()
            for file in self.files:
                if fnmatch.fnmatch(file,'*_movie.tdms') or fnmatch.fnmatch(file,'*.tif'):
                    self.fileList.append(file)
                    self.fileListWidget.addItem(os.path.basename(file))  
            self.displayedItem = self.fileListWidget.item(0)
            self.displayedItemChanged(0)
            self.displayedItem.setIcon(self.displayedIcon)
            #print(self.fileList)
            self.frameSlider.setValue(0) # Here, self.update() is called
            self.frameSlider.setMaximum(self.frames-1)
            self.setEnabled(True)
            
            if not self.trackingCheckBox.checkState():
                self.tabWidget.setEnabled(False)
            
            if self.exposure:
                self.framerateSpinBox.setValue(1/self.exposure)
                self.framerateSpinBox.setEnabled(False)
            else:
                self.framerateSpinBox.setValue(50) # default value
            
            if self.colormaps:
                self.colormapComboBox.setEnabled(True)
            self.scalingComboBox.setEnabled(True)
            self.enableLevels(False) 
                
            self.dir = os.path.dirname(self.files[0])
   
            
    def addFilesDialog(self):
        if not self.fileList:
            self.selectFilesDialog()
        else:
            if platform.system() == 'Darwin': # On MacOS the native file browser sometimes crashes
                options = QtWidgets.QFileDialog.DontUseNativeDialog
            else:
                options = QtWidgets.QFileDialog.Option()
            self.files, _ =  QtWidgets.QFileDialog.getOpenFileNames(self, 'Select Files...', self.dir, 'TDMS Files (*.tdms);;TIFF Files (*.tif)', options=options) # 'All Files (*)'
            if self.files:
                for file in self.files:
                    if fnmatch.fnmatch(file, '*_movie.tdms') or fnmatch.fnmatch(file, '*.tif'):
                        self.fileList.append(file)
                        self.fileListWidget.addItem(os.path.basename(file))   
            #print(self.fileList)
        
        
    def removeFiles(self):
        for item in self.fileListWidget.selectedItems():
            if item == self.displayedItem:
                self.clearGraphs()
            del self.fileList[self.fileListWidget.row(item)]
            self.fileListWidget.takeItem(self.fileListWidget.row(item))

        if not self.fileList:
            self.clearGraphs()
            self.setEnabled(False)
            
       # print(self.fileList)            
    
    def fileDoubleClicked(self, item):
        #self.displayedItem.setForeground(QtGui.QColor("black"))
        #item.setForeground(QtGui.QColor("red"))
        self.displayedItem.setIcon(QtGui.QIcon())
        item.setIcon(self.displayedIcon)
        self.displayedItem = item
        self.displayedItemChanged(self.fileListWidget.row(item))
     
        
    def displayedItemChanged(self, value):
        
        file = self.fileList[value]
        extension = os.path.splitext(file)[1]
        self.statusBar.showMessage('Loading: ' + os.path.basename(file))
        if extension == '.tdms':
            self.images = self.loadTDMSImages(file)
            self.propertiesLabel.setText('Dimensions: ' + str(self.dimx) + ' x ' + str(self.dimy) + ' x ' + str(self.frames) + '\n' + 'Binning: ' + str(self.binning) + '\n' + 'Exposure: ' + str(self.exposure) + ' s')
        if extension == '.tif':
            self.images = self.loadTIFFStack(file)
            self.propertiesLabel.setText('Dimensions: ' + str(self.dimx) + ' x ' + str(self.dimy) + ' x ' + str(self.frames))
        if self.frameSlider.value() == 0:
            self.update() 
        else:
            self.frameSlider.setValue(0) # Here, self.update() is called
        self.frameSlider.setMaximum(self.frames-1)
        self.frameSpinBox.setMaximum(self.frames-1)
        
        self.startFrameSpinBox.setMaximum(self.frames-1)
        self.startFrameSpinBox.setValue(0)
        self.endFrameSpinBox.setMaximum(self.frames-1)
        self.endFrameSpinBox.setValue(self.frames-1)
        
        self.p1.setRange(xRange=[0, self.dimx], yRange=[0, self.dimy])
        self.p2.setRange(xRange=[0, self.dimx], yRange=[0, self.dimy])
    
        lmaxmax = np.max(self.images) 
        self.lminSlider.setMaximum(lmaxmax)
        self.lminSpinBox.setMaximum(lmaxmax)
        self.lmaxSlider.setMaximum(lmaxmax)
        self.lmaxSpinBox.setMaximum(lmaxmax)
        
        #self.lminSlider.setValue(0)
        #self.lmaxSlider.setValue(lmaxmax)

        self.statusBar.showMessage('Ready')
        
        
    def loadTDMSImages(self, file):
        tdms_file = TdmsFile(file)
        p = tdms_file.object().properties
        self.dimx = int(p['dimx'])
        self.dimy = int(p['dimy'])
        self.binning = int(p['binning'])
        self.frames = int(p['dimz'])
        self.exposure = float(p['exposure'].replace(',', '.'))
        images = tdms_file.channel_data('Image', 'Image')
        return images.reshape(self.frames, self.dimy, self.dimx)
        
        
    def loadTIFFStack(self, file):
        images = io.imread(file)
        self.frames = images.shape[0]
        self.dimx = images.shape[1]
        self.dimy = images.shape[2]
        return images        
    
    
    def batchButtonClicked(self):
        self.trackingCheckBox.setCheckState(2)
        self.setEnabled(False)
        for item in self.fileListWidget.selectedItems():
            item.setSelected(False)

        self.batch = True
        self.selectFilesButton.setEnabled(False)
        self.addFilesButton.setEnabled(False)
        self.removeFilesButton.setEnabled(False)
        self.cancelButton.setEnabled(True)
        self.prefixH5 = self.prefixlineEdit.text()
        processedFrames = 0
        totalFrames = self.images.shape[0]*len(self.fileList) # estimate the total number of frames from the first file
       
        for f, file in enumerate(self.fileList):
            self.spots = pd.DataFrame()
            if self.fileListWidget.row(self.displayedItem) == 0 and f == 0:
                pass
            else:
                self.fileDoubleClicked(self.fileListWidget.item(f))
            self.statusBar.showMessage('Feature Detection... Progress: ' + os.path.basename(file))
            for j in range(self.images.shape[0]):
                self.frameSlider.setValue(j)
                processedFrames += 1
                self.progressBar.setValue(processedFrames/totalFrames*100)
                QtWidgets.QApplication.processEvents()
                if self.canceled:
                    self.progressBar.setValue(0)
                    self.statusBar.showMessage('Ready')
                    break
            
            
            # save metadata as data frame
            metadata = pd.DataFrame([{'dimx': self.dimx,
                                      'dimy': self.dimy,
                                      'frames': self.frames}])

            if os.path.splitext(file)[1] == '.tdms':
                metadata['binning'] =  self.binning
                metadata['exposure'] =  self.exposure
            
            if self.medianCheckBox.checkState():
                metadata['median'] = self.medianSpinBox.value()
            if self.subtractMeanCheckBox.checkState():
                metadata['subtract_mean'] = self.subtractMeanCheckBox.checkState()
            if self.maskCheckBox.checkState():
                metadata['maskX'] = self.maskXSpinBox.value()
                metadata['maskY'] = self.maskYSpinBox.value()
                metadata['maskR'] = self.maskRadiusSpinBox.value()
            
            metadata['method'] = self.tabWidget.tabText(self.tabIndex)
            for obj in self.tabWidget.currentWidget().findChildren(QtGui.QWidget):
                if obj.metaObject().className() == 'QSpinBox':
                    metadata[obj.objectName()] = obj.value();   
                if obj.metaObject().className() == 'QCheckBox':
                    metadata[obj.objectName()] = obj.checkState();
                     
                    
            # Save features and metadata in HDF5 file
            if self.hdf5:
                store = pd.HDFStore(os.path.splitext(file)[0].replace('_movie', '') + self.prefixH5 + '_features.h5', 'w')
                store.put('features', self.spots)
                store.put('metadata', metadata)
                store.close()
                
            # Save metadata and features as CSV file
            if self.csv:
                file = os.path.splitext(file)[0].replace('_movie', '') + self.prefixH5 + '_features.csv'
                metadata.to_csv(file, mode='w')   
                self.spots.to_csv(file, mode='a')
            
            if self.canceled:
                break
            
        self.setEnabled(True)
        self.selectFilesButton.setEnabled(True)
        self.addFilesButton.setEnabled(True)
        self.removeFilesButton.setEnabled(True)
        self.cancelButton.setEnabled(False)
        if not self.canceled:
            self.progressBar.setValue(100)
            self.statusBar.showMessage('Ready')
        self.batch = False
        self.canceled = False
  
    
    def exportButtonClicked(self):

        self.setEnabled(False)
        for item in self.fileListWidget.selectedItems():
            item.setSelected(False)

        self.cancelButton.setEnabled(True)
        self.canceled = False
        self.selectFilesButton.setEnabled(False)
        self.addFilesButton.setEnabled(False)
        self.removeFilesButton.setEnabled(False)
        self.batchButton.setEnabled(False)
        self.exportButton.setEnabled(False)
        
        if os.path.splitext(self.fileList[0])[1] == '.tdms':
            filename = os.path.splitext(self.fileList[0])[0].replace('_movie', '') + '.mp4'
        if os.path.splitext(self.fileList[0])[1] == '.tif':
            filename = os.path.splitext(self.fileList[0])[0] + '.mp4'
        
        commands = ['FFmpeg/ffmpeg',
                    '-loglevel', 'quiet',
                    '-y',  # (optional) overwrite output file if it exists
                    '-f', 'image2pipe',
                    '-vcodec', 'png',
                    '-r', str(self.framerateSpinBox.value()),  # frames per second
                    '-i', '-',  # The input comes from a pipe
                    '-pix_fmt', 'yuv420p',
                    '-vcodec', 'libx264',
                    '-qscale', '0',
                    filename]
        
        pipe = sp.Popen(commands, stdin=sp.PIPE)
        
        processedFrames = 0
        totalFrames = self.images.shape[0]*len(self.fileList) # estimate the total number of frames from the first file
            
        for f, file in enumerate(self.fileList):  
            if (f == 0 and self.fileListWidget.row(self.displayedItem) == 0) or self.exportTypeComboBox.currentIndex() == 0:
                if self.exportTypeComboBox.currentIndex() == 0:
                    totalFrames = self.endFrameSpinBox.value() - self.startFrameSpinBox.value() + 1
            else:
                self.fileDoubleClicked(self.fileListWidget.item(f)) 
            self.statusBar.showMessage('Video Export... Progress: ' + os.path.basename(file))
            for i in range(self.startFrameSpinBox.value(), self.endFrameSpinBox.value()):
                self.frameSlider.setValue(i)
                if self.exportViewComboBox.currentIndex() == 0: 
                    exporter = pg.exporters.ImageExporter(self.im1)
                else:
                    exporter = pg.exporters.ImageExporter(self.im2)
                exporter.params.param('width').setValue(500, blockSignal=exporter.widthChanged)
                exporter.params.param('height').setValue(500, blockSignal=exporter.heightChanged)
                buffer = QtCore.QBuffer()
                buffer.open(QtCore.QIODevice.ReadWrite)
                exporter.export(toBytes=True).save(buffer, 'PNG')
                pipe.stdin.write(buffer.data())
                processedFrames += 1
                self.progressBar.setValue(processedFrames/totalFrames*100)
                QtWidgets.QApplication.processEvents()
                if self.canceled:
                    pipe.stdin.close()
                    pipe.wait()
                    self.progressBar.setValue(0)
                    self.statusBar.showMessage('Ready')
                    break
            if self.exportTypeComboBox.currentIndex() == 0:
                break
        pipe.stdin.close()
        pipe.wait()
        self.progressBar.setValue(100)
        self.statusBar.showMessage('Ready')
        
        self.setEnabled(True)
        self.selectFilesButton.setEnabled(True)
        self.addFilesButton.setEnabled(True)
        self.removeFilesButton.setEnabled(True)
        self.batchButton.setEnabled(True)
        self.exportButton.setEnabled(True)
        self.cancelButton.setEnabled(False)
        
                
    def exportTypeComboBoxChanged(self):
        if self.exportTypeComboBox.currentIndex() == 0:
            self.startFrameSpinBox.setValue(0)
            self.startFrameSpinBox.setEnabled(True)
            self.endFrameSpinBox.setValue(self.frames-1)
            self.endFrameSpinBox.setEnabled(True)
        else:
            self.startFrameSpinBox.setValue(0)
            self.startFrameSpinBox.setEnabled(False)
            self.endFrameSpinBox.setValue(self.frames-1)
            self.endFrameSpinBox.setEnabled(False)
        
    def abortButtonClicked(self):
        self.abort = True
       
        
    def trackingCheckBoxChanged(self):
        if self.trackingCheckBox.checkState():
            self.tabWidget.setEnabled(True)
        else:
            self.tabWidget.setEnabled(False)
            self.im2.setLookupTable(self.colormaps[self.colormapComboBox.currentIndex()])
        self.update()

    def cancelClicked(self, e):
        self.canceled = True

    def closeEvent(self, e):
        # Save the current settings in the TrackerLab.ini file
        self.saveSettings()
        e.accept()
        
        
    def saveSettings(self):
        self.settings.setValue('Dir', self.dir)
        self.settings.setValue('TabIndex', self.tabWidget.currentIndex())
        self.settings.setValue('TrackingState', self.trackingCheckBox.checkState())
        self.settings.setValue('Pre-Processing/medianState', self.medianCheckBox.checkState())
        self.settings.setValue('Pre-Processing/subtractMeanState', self.subtractMeanCheckBox.checkState())
        self.settings.setValue('Pre-Processing/medianSize', self.medianSpinBox.value())
        self.settings.setValue('Pre-Processing/maskState', self.maskCheckBox.checkState())
        self.settings.setValue('Pre-Processing/maskX', self.maskXSpinBox.value())
        self.settings.setValue('Pre-Processing/maskY', self.maskYSpinBox.value())
        self.settings.setValue('Pre-Processing/maskRadius', self.maskRadiusSpinBox.value())
        self.settings.setValue('Settings/HDF5', self.hdf5)
        self.settings.setValue('Settings/CSV', self.csv)
        self.settings.setValue('Video/exportTypeComboBox', self.exportTypeComboBox.currentIndex())
        self.settings.setValue('Video/exportViewComboBox', self.exportViewComboBox.currentIndex())
        
        for tabCount in range(self.tabWidget.count()):
            tab = self.tabWidget.widget(tabCount);
            for obj in tab.findChildren(QtGui.QWidget):
                if obj.metaObject().className() == 'QSpinBox':
                    self.settings.setValue('Tab' + str(tabCount + 1) + '/' + obj.objectName(), str(obj.value()))
                if obj.metaObject().className() == 'QCheckBox':
                    self.settings.setValue('Tab' + str(tabCount + 1) + '/' + obj.objectName(), str(obj.checkState()))
                    
        
    def restoreSettings(self):
        if os.path.isfile('TrackerLab.ini'):
            self.settings = QSettings('TrackerLab.ini', QSettings.IniFormat) # Opens 'TrackerLab.ini' 
            for tabCount in range(self.tabWidget.count()):
                tab = self.tabWidget.widget(tabCount);
                for obj in tab.findChildren(QtGui.QWidget):
                    if obj.metaObject().className() == 'QSpinBox':
                        obj.setValue(int(self.settings.value('Tab' + str(tabCount + 1) + '/' + obj.objectName())))
                    if obj.metaObject().className() == 'QCheckBox':
                        obj.setCheckState(int(self.settings.value('Tab' + str(tabCount + 1) + '/' + obj.objectName())))
        else:
            self.settings = QSettings('TrackerLab.ini', QSettings.IniFormat) # Creates 'TrackerLab.ini' 

        self.dir = self.settings.value('Dir', '.')
        self.trackingCheckBox.setCheckState(int(self.settings.value('TrackingState', '2')))
        self.tabWidget.setCurrentIndex(int(self.settings.value('TabIndex', '0'))) 
        self.medianCheckBox.setCheckState(int(self.settings.value('Pre-Processing/medianState', '0')))
        self.medianCheckBox.setCheckState(int(self.settings.value('Pre-Processing/subtractMeanState', '0')))
        self.medianSpinBox.setValue(int(self.settings.value('Pre-Processing/medianValue', '2'))) 
        self.maskCheckBox.setCheckState(int(self.settings.value('Pre-Processing/maskState', '0')))
        self.maskXSpinBox.setValue(int(self.settings.value('Pre-Processing/maskX', '100')))  
        self.maskYSpinBox.setValue(int(self.settings.value('Pre-Processing/maskY', '100')))  
        self.maskRadiusSpinBox.setValue(int(self.settings.value('Pre-Processing/maskRadius', '100')))  
        self.hdf5 = int(self.settings.value('Settings/HDF5', '1'))
        self.csv = int(self.settings.value('Settings/CSV', '0'))
        
        self.exportTypeComboBox.setCurrentIndex(int(self.settings.value('Video/exportTypeComboBox', '0')))
        self.exportViewComboBox.setCurrentIndex(int(self.settings.value('Video/exportViewComboBox', '0')))

    def clearGraphs(self):
        self.im1.clear()
        self.im2.clear()
        #self.sp1.clear()
        self.lp1.clear()
        self.lp2.clear()
        
    def setEnabled(self, state):
        self.fileListWidget.setEnabled(state)
        self.frameSlider.setEnabled(state)
        self.frameSpinBox.setEnabled(state)
        self.colormapComboBox.setEnabled(state)
        self.scalingComboBox.setEnabled(state)
        self.maskComboBox.setEnabled(state)
        self.enableLevels(state) 
        self.batchButton.setEnabled(state)
        self.preprocessingFrame.setEnabled(state)
        if self.ffmpeg:
            self.exportFrame.setEnabled(state)
            self.exportButton.setEnabled(state)
        if self.exportTypeComboBox.currentIndex() == 1:
            self.startFrameSpinBox.setEnabled(False)
            self.endFrameSpinBox.setEnabled(False)
        self.trackingCheckBox.setEnabled(state)
        self.tabWidget.setEnabled(state)
        self.removeFilesButton.setEnabled(state)


    def enableLevels(self, state): 
       self.lminSlider.setEnabled(state)  
       self.lminSpinBox.setEnabled(state) 
       self.lmaxSlider.setEnabled(state)  
       self.lmaxSpinBox.setEnabled(state) 
      
    def showSettingsWindow(self):
        if self.settingsWindow.exec_() == QtGui.QDialog.Accepted:
            self.hdf5 = self.settingsWindow.radioButtonHDF5.isChecked()
            self.csv = self.settingsWindow.radioButtonCSV.isChecked()
        else: # Rejected 
            self.settingsWindow.radioButtonHDF5.setChecked(self.hdf5)
            self.settingsWindow.radioButtonCSV.setChecked(self.csv)
            
    def aboutClicked(self):
       about = QMessageBox()
       about.setWindowTitle("About")
       about.setTextFormat(QtCore.Qt.RichText)   
       about.setText("This is the Molecular Nanophotonics TrackerLab. " +
                     "It is based on PyQt and the PyQtGraph libary." + 2*"<br>" +
                     "<a href='http://github.com/Molecular-Nanophotonics/TrackerLab'>http://github.com/molecular-nanophotonics/trackerlab</a>" + 2*"<br>" +
                     "M. Fränzl and N. Söker")
       about.exec()

     
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec_())
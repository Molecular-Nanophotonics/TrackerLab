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
from pyqtgraph import QtCore, QtGui
#import inspect

from matplotlib import cm # for colormaps

import numpy as np

import pandas as pd
import skimage
#from skimage import io
from skimage import morphology      
from skimage.util import invert

from scipy import ndimage
import os, fnmatch, glob

from nptdms import TdmsFile

import Modules


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
        
        # restore setting from TrackerLab.ini file
        self.restoreSettings() 
        
        self.selectFilesButton.clicked.connect(self.selectFilesDialog)
        self.addFilesButton.clicked.connect(self.addFilesDialog)
        self.removeFilesButton.clicked.connect(self.removeFiles)
        
        self.fileList = []
        self.fileListWidget.itemDoubleClicked.connect(self.fileDoubleClicked)
        
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
        self.abortButton.clicked.connect(self.abortButtonClicked)
        self.abort = False
 
        self.medianCheckBox.stateChanged.connect(self.update)  
        self.medianSpinBox.valueChanged.connect(self.update)
        self.maskCheckBox.stateChanged.connect(self.update)
        self.maskXSpinBox.valueChanged.connect(self.maskChanged)
        self.maskYSpinBox.valueChanged.connect(self.maskChanged)
        self.maskRadiusSpinBox.valueChanged.connect(self.maskChanged)
        self.mask = np.array([])
        
        self.trackingCheckBox.stateChanged.connect(self.trackingCheckBoxChanged)
        self.tabWidget.currentChanged.connect(self.update) 
        self.tabIndex = 0
        
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
        #self.abortProgressButton = QtGui.QPushButton("Abort")
        #self.statusBar.addPermanentWidget(self.abortProgressButton)
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
            self.colormapsComboBox.addItem('Gray') # default
        else:
            self.colormapComboBox.setCurrentIndex(self.colormapComboBox.findText('Gray'))
          
        #pg.SignalProxy(self.p.scene().sigMouseMoved, rateLimit=60, slot=self.mouseMoved)
        #pg.SignalProxy(self.p2.scene().sigMouseMoved, rateLimit=60, slot=self.mouseMoved)
        
        self.settingsWindow = SettingsWindow() 
        self.settingsWindow.checkBoxHDF5.setChecked(self.hdf5)
        self.settingsWindow.checkBoxCSV.setChecked(self.csv)
        #self.settingsWindow.hdf5 = self.hdf5 
        #self.settingsWindow.csv = self.csv
        
        #pixmap = QtGui.QPixmap(32, 32)
        #pixmap.fill(QtCore.Qt.white)
        #painter = QtGui.QPainter(pixmap)
        #painter.setBrush(QtCore.Qt.black)
        #painter.drawEllipse(QtCore.QPoint(16, 16), 5, 5)
        #self.displayedIcon = QtGui.QIcon(pixmap)
        
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
        if self.medianCheckBox.checkState():
            self.processedImage = ndimage.median_filter(self.processedImage, self.medianSpinBox.value())
            
        if self.maskCheckBox.checkState():
            if not self.mask.shape[0] == self.dimx or not self.mask.shape[1] == self.dimy:
                self.maskChanged()
            self.processedImage = self.mask*self.processedImage
        
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
        xx, yy= np.meshgrid(np.arange(0, self.dimx, 1), np.arange(0, self.dimy, 1))
        self.mask = (((xx - x0)**2 + (yy - y0)**2) < (diameter/2)**2).astype(int)
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
        
        
    def fileComboBoxChanged(self, value):
        
        file = self.fileList[value]
        extension = os.path.splitext(file)[1]
        self.statusBar.showMessage('...')
        if extension == '.tdms':
            self.images = self.loadTDMSImages(file)
        if extension == '.tif':
            self.images = self.loadTIFFStack(file)
        if self.frameSlider.value() == 0:
            self.update() 
        else:
            self.frameSlider.setValue(0) # Here, self.update() is called
        self.frameSlider.setMaximum(self.frames-1)
        self.frameSpinBox.setMaximum(self.frames-1)
        #self.p.setLimits(xMax=self.dimx, yMax=self.dimy)
        self.p1.setRange(xRange=[0, self.dimx], yRange=[0, self.dimy])
        #self.p2.setLimits(xMax=self.dimx, yMax=self.dimy)
        self.p2.setRange(xRange=[0, self.dimx], yRange=[0, self.dimy])
        
        lmaxmax = np.max(self.images) 
        self.lminSlider.setMaximum(lmaxmax)
        self.lminSpinBox.setMaximum(lmaxmax)
        self.lmaxSlider.setMaximum(lmaxmax)
        self.lmaxSpinBox.setMaximum(lmaxmax)
        self.lminSlider.setValue(0)
        self.lmaxSlider.setValue(lmaxmax)

        self.statusBar.showMessage('Ready')



    def selectFilesDialog(self):
        self.files, _ =  QtWidgets.QFileDialog.getOpenFileNames(self, 'Select Files...', self.dir, 'TDMS Files (*.tdms);;TIFF Files (*.tif)') # 'All Files (*)'
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
            self.propertiesLabel.setText('Dimensions: ' + str(self.dimx) + ' x ' + str(self.dimy) + ' x ' + str(self.frames) + '\n' + 'Binning: ' + str(self.binning) + '\n' + 'Exposure: ' + str(self.exposure) + ' s')
            self.setEnabled(True)
            if self.colormaps:
                self.colormapComboBox.setEnabled(True)
            self.scalingComboBox.setEnabled(True)
            if self.scalingComboBox.currentIndex():
                self.enableLevels(True) 
            self.dir = os.path.dirname(self.files[0])
   
            
    def addFilesDialog(self):
        if not self.fileList:
            self.selectFilesDialog()
        else:     
            self.files, _ =  QtWidgets.QFileDialog.getOpenFileNames(self, 'Select Files...', self.dir, 'TDMS Files (*.tdms);;TIFF Files (*.tif)') # 'All Files (*)'
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
        self.statusBar.showMessage('...')
        if extension == '.tdms':
            self.images = self.loadTDMSImages(file)
        if extension == '.tif':
            self.images = self.loadTIFFStack(file)
        if self.frameSlider.value() == 0:
            self.update() 
        else:
            self.frameSlider.setValue(0) # Here, self.update() is called
        self.frameSlider.setMaximum(self.frames-1)
        self.frameSpinBox.setMaximum(self.frames-1)
        #self.p.setLimits(xMax=self.dimx, yMax=self.dimy)
        self.p1.setRange(xRange=[0, self.dimx], yRange=[0, self.dimy])
        #self.p2.setLimits(xMax=self.dimx, yMax=self.dimy)
        self.p2.setRange(xRange=[0, self.dimx], yRange=[0, self.dimy])
        
        lmaxmax = np.max(self.images) 
        self.lminSlider.setMaximum(lmaxmax)
        self.lminSpinBox.setMaximum(lmaxmax)
        self.lmaxSlider.setMaximum(lmaxmax)
        self.lmaxSpinBox.setMaximum(lmaxmax)
        self.lminSlider.setValue(0)
        self.lmaxSlider.setValue(lmaxmax)

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
        return images.reshape(self.frames, self.dimx, self.dimy)
        
        
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
        self.abortButton.setEnabled(True)
        processedFrames = 0
        totalFrames = self.images.shape[0]*len(self.fileList) # estimate the total number of frames from the first file
        for i, imageFile in enumerate(self.fileList):
            self.spots = pd.DataFrame()
            if self.fileListWidget.row(self.displayedItem) == 0 and i == 0:
                #self.fileDoubleClicked(self.fileListWidget.item(0))
                print('Test')
            else:
                self.fileDoubleClicked(self.fileListWidget.item(i))
            self.statusBar.showMessage('Batch...')
            for j in range(self.images.shape[0]):
                self.frameSlider.setValue(j)
                processedFrames += 1
                self.progressBar.setValue(processedFrames/totalFrames*100)
                QtWidgets.QApplication.processEvents()
                if self.abort:
                    self.progressBar.setValue(0)
                    self.statusBar.showMessage('Ready')
                    break
                
            if self.hdf5:
                store = pd.HDFStore(os.path.splitext(imageFile)[0].replace('_movie', '') + '_features.h5', 'w')

                store.put('spots', self.spots)
                
                # save metadata as data frame
                metadata = pd.DataFrame([{'dimx': self.dimx,
                                          'dimy': self.dimx,
                                          'binning': self.binning,
                                          'frames': self.frames,
                                          'exposure': self.exposure}])
                
                if self.medianCheckBox.checkState():
                    metadata['median'] = self.medianSpinBox.value()
                if self.maskCheckBox.checkState():
                    metadata['maskX'] = self.maskXSpinBox.value()
                    metadata['maskY'] = self.maskYSpinBox.value()
                    metadata['maskR'] = self.maskRadiusSpinBox.value()
                
                # self.tabWidget.currentWidget() is same as self.tabWidget.widget(self.tabWidget.currentIndex())
                
                metadata['method'] = self.tabWidget.tabText(self.tabIndex)
                for obj in self.tabWidget.currentWidget().findChildren(QtGui.QWidget):
                    if obj.metaObject().className() == 'QSpinBox':
                        metadata[obj.objectName()] = obj.value();   
                    if obj.metaObject().className() == 'QCheckBox':
                        metadata[obj.objectName()] = obj.checkState();     
                    
                store.put('metadata', metadata)
                store.close()
                
                
            if self.csv: # save as csv file
                file = os.path.splitext(imageFile)[0].replace('_movie', '') + '_spots.csv'
                with open(file, 'w') as f:
                    f.write('# dimx,dimy,frames,binning\n')
                    f.write('# %d,%d,%d,%d\n' % (self.dimx, self.dimy, self.frames, self.binning))

                self.spots.to_csv(file, mode='a')
            
            if self.abort:
                break
            
        self.setEnabled(True)
        self.selectFilesButton.setEnabled(True)
        self.addFilesButton.setEnabled(True)
        self.removeFilesButton.setEnabled(True)
        self.abortButton.setEnabled(False)
        if not self.abort:
            self.progressBar.setValue(100)
            self.statusBar.showMessage('Ready')
        self.batch = False
        self.abort = False
  
        
        
    def abortButtonClicked(self):
        self.abort = True
       
        
    def trackingCheckBoxChanged(self):
        if self.trackingCheckBox.checkState():
            self.tabWidget.setEnabled(True)
        else:
            self.tabWidget.setEnabled(False)
            self.im2.setLookupTable(self.colormaps[self.colormapComboBox.currentIndex()])
        self.update()
        
        
    def closeEvent(self, e):
        # Save the current settings in the TrackerLab.ini file
        self.saveSettings()
        e.accept()
        
        
    def saveSettings(self):
        self.settings.setValue('Dir', self.dir)
        self.settings.setValue('TabIndex', self.tabWidget.currentIndex())
        self.settings.setValue('TrackingState', self.trackingCheckBox.checkState())
        self.settings.setValue('Pre-Processing/MedianState', self.medianCheckBox.checkState())
        self.settings.setValue('Pre-Processing/MedianValue', self.medianSpinBox.value())
        self.settings.setValue('Pre-Processing/MaskState', self.maskCheckBox.checkState())
        self.settings.setValue('Pre-Processing/MaskX', self.maskXSpinBox.value())
        self.settings.setValue('Pre-Processing/MaskY', self.maskYSpinBox.value())
        self.settings.setValue('Pre-Processing/MaskRadius', self.maskRadiusSpinBox.value())
        self.settings.setValue('Settings/HDF5', self.hdf5)
        self.settings.setValue('Settings/CSV', self.csv)
        
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
        self.tabWidget.setCurrentIndex(int(self.settings.value('tabIndex', '0'))) 
        self.medianCheckBox.setCheckState(int(self.settings.value('Pre-Processing/MedianState', '0')))
        self.medianSpinBox.setValue(int(self.settings.value('Pre-Processing/MedianValue', '2'))) 
        self.maskCheckBox.setCheckState(int(self.settings.value('Pre-Processing/MaskState', '0')))
        self.maskXSpinBox.setValue(int(self.settings.value('Pre-Processing/MaskX', '100')))  
        self.maskYSpinBox.setValue(int(self.settings.value('Pre-Processing/MaskY', '100')))  
        self.maskRadiusSpinBox.setValue(int(self.settings.value('Pre-Processing/MaskRadius', '100')))  
        self.hdf5 = int(self.settings.value('Settings/HDF5', '2'))
        self.csv = int(self.settings.value('Settings/CSV', '0'))

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
        self.batchButton.setEnabled(state)
        self.preprocessingFrame.setEnabled(state)
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
            self.hdf5 = self.settingsWindow.checkBoxHDF5.checkState()
            self.csv = self.settingsWindow.checkBoxCSV.checkState()
        else: # Rejected 
            self.settingsWindow.checkBoxHDF5.setChecked(self.hdf5)
            self.settingsWindow.checkBoxCSV.setChecked(self.csv)
            
        print(self.hdf5, self.csv)
            
       
    def aboutClicked(self):
       about = QMessageBox()
       about.setWindowTitle("About")
       about.setTextFormat(QtCore.Qt.RichText)   
       about.setText("This is the Molecular Nanophotonics TrackerLab. " +
                     "It is based on PyQt and the PyQtGraph libary." + 2*"<br>" +
                     "<a href='http://github.com/Molecular-Nanophotonics/TrackerLab'>http://github.com/molecular-nanophotonics/trackerlab</a>" + 2*"<br>" +
                     "M. Fränzl and N. Söcker")
       about.exec()

     
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec_())
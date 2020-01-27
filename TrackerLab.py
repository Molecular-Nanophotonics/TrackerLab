# -*- coding: utf-8 -*-
"""
Discription: This is the Molecular Nanophotonics TrackLab.
Author(s): M. Fränzl, N. Söker
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

import imageio
from nptdms import TdmsFile

import subprocess as sp # for calling ffmpeg

import ScaleBar, Modules

import platform

class Preferences(QDialog):
    def __init__(self):
        super().__init__(None,  QtCore.Qt.WindowCloseButtonHint)
        
        loadUi('Preferences.ui', self)
        
        self.okButton.clicked.connect(self.accept)
        self.cancelButton.clicked.connect(self.reject)
        
        
class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.ui = loadUi('TrackerLab.ui', self)        
        self.preferences = Preferences()
        
        self.scaleBar1 = ScaleBar.ScaleBar();
        self.scaleBar2 = ScaleBar.ScaleBar();
    
        self.displayedIcon = QtGui.QIcon(QtGui.QPixmap("Resources/Circle.png")) 
        ## draw the icon  
        #pixmap = QtGui.QPixmap(32, 32)
        #pixmap.fill(QtCore.Qt.white)
        #painter = QtGui.QPainter(pixmap)
        #painter.setBrush(QtCore.Qt.black)
        #painter.drawEllipse(QtCore.QPoint(16, 16), 5, 5)
        #self.displayedIcon = QtGui.QIcon(pixmap)
        
        # Restore setting from TrackerLab.ini file
        if self.restoreSettings():
            print('An error occured opening the INI file. A new INI file will be created on closing.')
        else:
            print(self.settings.fileName())
            
        self.filterList = ['TDMS Files (*.tdms)', 'TIFF Files (*.tif)', 'MP4 Files (*.mp4)']
        
        self.preferences.radioButtonHDF5.setChecked(self.hdf5)
        self.preferences.radioButtonCSV.setChecked(self.csv)
        self.selectFilesButton.clicked.connect(self.selectFiles)
        self.addFilesButton.clicked.connect(self.appendFiles)
        self.removeFilesButton.clicked.connect(self.removeFiles)
        
        self.fileList = []
        self.fileListWidget.itemDoubleClicked.connect(self.fileDoubleClicked)
        self.exposure = []
        
        self.frameSlider.valueChanged.connect(self.frameSliderChanged)   
        self.frameSpinBox.valueChanged.connect(self.frameSpinBoxChanged)  
      
        self.colormapComboBox.currentIndexChanged.connect(self.colormapComboBoxChanged) 
        self.scalingComboBox.currentIndexChanged.connect(self.scalingComboBoxChanged) 
        
        self.cminSlider.valueChanged.connect(self.cminSliderChanged)   
        self.cminSpinBox.valueChanged.connect(self.cminSpinBoxChanged)  
        self.cmaxSlider.valueChanged.connect(self.cmaxSliderChanged)   
        self.cmaxSpinBox.valueChanged.connect(self.cmaxSpinBoxChanged)  
        
        self.batchButton.clicked.connect(self.batchButtonClicked)
 
        self.medianCheckBox.stateChanged.connect(self.update)  
        self.subtractMeanCheckBox.stateChanged.connect(self.update)  
        self.medianSpinBox.valueChanged.connect(self.update)
        self.softwareBinningSpinBox.valueChanged.connect(self.update)
        self.maskCheckBox.stateChanged.connect(self.maskCheckBoxChanged)
        self.maskTypeComboBox.currentIndexChanged.connect(self.maskTypeChanged) 
        self.roiCheckBox.stateChanged.connect(self.roiCheckBoxChanged)
        
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
        self.actionSettings.triggered.connect(self.showPreferences)
        self.actionAbout.triggered.connect(self.aboutClicked)

        self.scaleBar1Button.clicked.connect(self.scaleBar1.showSettingsDialog)
        self.scaleBar1CheckBox.stateChanged.connect(self.scaleBar1.setVisible)
        self.scaleBar2Button.clicked.connect(self.scaleBar2.showSettingsDialog)
        self.scaleBar2CheckBox.stateChanged.connect(self.scaleBar2.setVisible)

    
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
    
        self.roi = 0  # Important for start-up
        self.maskROI = 0
        
        self.exportVideoButton.clicked.connect(self.exportVideoButtonClicked)
        self.exportImageButton.clicked.connect(self.exportImageButtonClicked)
        
        # Items for overlay
        
        #self.sp1 = pg.ScatterPlotItem(pen=pg.mkPen('r', width=3), brush=pg.mkBrush(None), pxMode=False)
        #self.p2.addItem(self.sp1)
        
        self.lp1 = pg.PlotCurveItem(pen=pg.mkPen('b', width=3), brush=pg.mkBrush(None), pxMode=False)  
        self.p2.addItem(self.lp1)

        self.lp2 = pg.PlotCurveItem(pen=pg.mkPen('r', width=3), brush=pg.mkBrush(None), pxMode=False)
        self.p2.addItem(self.lp2)
                
        self.scaleBar1.add(self.p1)
        self.scaleBar2.add(self.p2)

        
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
        
        # Load colormaps        
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
        
        self.infoLabel.setTextFormat(QtCore.Qt.RichText) 
        
        # Check if FFmpeg is available
        self.ffmpeg = True

        try:
            if platform.system() == 'Darwin': # On MacOS the rights for the ffmpeg file have to changed 
                os.chdir('FFmpeg')
                os.chmod('ffmpeg', 0o777) # "0o" is needed since chmod expects octal integers
                os.chdir('..')
            sp.call(['FFmpeg/ffmpeg'])
            
        except:
            self.ffmpeg = False # FFmpeg is not installed
            print('FFmpeg is Not Installed. Video Export is Disabled.')
        
        self.exportVideo = False
        
        
    def mouseMoved(self, e):
        if self.p1.vb.sceneBoundingRect().contains(e):
            mousePoint = self.p1.vb.mapSceneToView(e)
            x = int(mousePoint.x())
            y = int(mousePoint.y()) 
            if x > 0 and x < self.dimx and y > 0 and y < self.dimy:
                self.mouseLabel.setText("x = %d\ty = %d\t[%d]" % (x, y, self.images[self.frameSlider.value(), y ,x]))
                
        if self.p2.vb.sceneBoundingRect().contains(e):
            mousePoint = self.p2.vb.mapSceneToView(e)  
            x = int(mousePoint.x())
            y = int(mousePoint.y()) 
            if x > 0 and x < self.processedImage.shape[1] and y > 0 and y < self.processedImage.shape[0]:
                self.mouseLabel.setText("x = %d\ty = %d\t[%d]" % (x, y, self.processedImage[y, x]))
                
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
            self.im1.setImage(self.images[self.frameSlider.value()], levels=[self.cminSlider.value(), self.cmaxSlider.value()])             
        
        self.processedImage = self.images[self.frameSlider.value()]
        
        if self.roiCheckBox.checkState():
            self.processedImage = self.roi.getArrayRegion(self.processedImage, img=self.im1)
            self.roiChanged()
                  
        # Image Pre-Processing 
        def rebin_image(arr_in,binning):
            # Throw away the last rows and cols 
            new_shape = tuple(np.array(arr_in.shape)//binning)
            arr = arr_in[:binning*new_shape[0],:binning*new_shape[1]]
            shape = (new_shape[0], arr.shape[0] // new_shape[0],
                     new_shape[1], arr.shape[1] // new_shape[1])
            return arr.reshape(shape).mean(-1).mean(1)
        self.processedImage = rebin_image(self.processedImage, self.softwareBinningSpinBox.value())
        
        if self.subtractMeanCheckBox.checkState():
            self.processedImage = self.processedImage - self.meanSeriesImage
            self.processedImage[self.processedImage<0] = 0
        
        if self.medianCheckBox.checkState():
            self.processedImage = ndimage.median_filter(self.processedImage, self.medianSpinBox.value())
            
        if self.maskCheckBox.checkState() and self.maskROI:
            self.maskChanged()
            self.processedImage = self.mask*self.processedImage
        
        #skimage.io.imsave('image.tif',self.processedImage)
        
        # Tracking
        spots = pd.DataFrame()
        if self.trackingCheckBox.checkState():
            spots = self.findFeatures(self.frameSlider.value())   

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
                self.im2.setImage(self.processedImage, levels=[self.cminSlider.value(), self.cmaxSlider.value()])
            self.lp1.clear()
            self.lp2.clear()
        
        if self.batch:
            self.spots = self.spots.append(spots)
            
        #self.sp.setData(x=spots.x.tolist(), y=spots.y.tolist(), size=10)
                
     # Tracking     
    def findFeatures(self, i):
        
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

       
    def maskTypeChanged(self):
        if self.maskTypeComboBox.currentIndex() == 0:
            self.p1.removeItem(self.maskROI)
            self.maskROI = pg.CircleROI([self.maskX, self.maskY], [self.maskW, self.maskH], maxBounds=QtCore.QRectF(0, 0, self.dimx, self.dimy), pen=(0, 10), scaleSnap=True, translateSnap=True)
            self.maskROI.sigRegionChanged.connect(self.update)
            self.p1.addItem(self.maskROI)
        else:
            self.p1.removeItem(self.maskROI)
            self.maskROI = pg.RectROI([self.maskX, self.maskY], [self.maskW, self.maskH], maxBounds=QtCore.QRectF(0, 0, self.dimx, self.dimy), pen=(0, 10), scaleSnap=True, translateSnap=True)
            self.maskROI.sigRegionChanged.connect(self.update)
            self.p1.addItem(self.maskROI)
        self.update()
        
    def maskCheckBoxChanged(self):
         # If the mask bounds are larger than the image set ROI to the size of the image (This might be the case if a smaller image displayed) 
        if self.maskX > self.dimx or self.maskX + self.maskW > self.dimx or self.maskY > self.dimy or self.maskY + self.maskH > self.dimy:
            self.maskX = 0; self.maskY = 0; self.maskW = self.dimx; self.maskH = self.dimy 
        if self.maskROI and self.maskCheckBox.checkState():
           self.p1.removeItem(self.maskROI)
           self.maskROI = 0   
        if not self.maskROI and self.maskCheckBox.checkState():
            if self.maskTypeComboBox.currentIndex() == 0:
                self.maskROI = pg.CircleROI([self.maskX, self.maskY], [self.maskW, self.maskH], maxBounds=QtCore.QRectF(0, 0, self.dimx, self.dimy), pen=(0, 10), scaleSnap=True, translateSnap=True)
            else:
                self.maskROI = pg.RectROI([self.maskX, self.maskY], [self.maskW, self.maskH], maxBounds=QtCore.QRectF(0, 0, self.dimx, self.dimy), pen=(0, 10), scaleSnap=True, translateSnap=True)                 
            self.maskROI.sigRegionChanged.connect(self.update)
            self.p1.addItem(self.maskROI)
            self.maskTypeComboBox.setEnabled(True)
            self.maskLabel.setVisible(True)
        else:
            self.p1.removeItem(self.maskROI)
            self.maskROI = 0
            self.maskTypeComboBox.setEnabled(False)
            self.maskLabel.setVisible(False)
        self.update()
        
        
    def maskChanged(self):
            if self.roiCheckBox.checkState():
                xx, yy= np.meshgrid(np.arange(self.roiX, self.roiX + self.roiW, 1), np.arange(self.roiY, self.roiY + self.roiH, 1))
            else:
                xx, yy= np.meshgrid(np.arange(0, self.dimx, 1), np.arange(0, self.dimy, 1))
            if self.maskTypeComboBox.currentIndex() == 0:
                self.maskX, self.maskY = self.maskROI.pos()
                self.maskW, self.maskH = self.maskROI.size()
                self.mask = (((xx - self.maskX - (self.maskW-1)/2)**2 + (yy - self.maskY - (self.maskH-1)/2)**2) < ((self.maskW)/2)**2).astype(int)
            if self.maskTypeComboBox.currentIndex() == 1:
                self.maskX, self.maskY =  self.maskROI.pos()
                self.maskW, self.maskH = self.maskROI.size()
                self.mask = ((np.abs(xx - self.maskX - self.maskW/2 + 1) <= (self.maskW+1)/2) & (np.abs(yy - self.maskY - self.maskH/2 + 1) <= (self.maskH+1)/2)).astype(int)
            
            self.maskLabel.setText("<font color='#ff0000'>Mask: (%d, %d) (%d, %d)</font>" % (self.maskX, self.maskY, self.maskW, self.maskH))
            
    def roiCheckBoxChanged(self):
        # If the ROI bounds larger than the image set ROI to the size of the image (This might be the case if a smaller image displayed) 
        if self.roiX > self.dimx or self.roiX + self.roiW > self.dimx or self.roiY > self.dimy or self.roiY + self.roiH > self.dimy:
           self.roiX = 0; self.roiY = 0; self.roiW = self.dimx; self.roiH = self.dimy 
        if self.roi and self.roiCheckBox.checkState():
            self.p1.removeItem(self.roi)
            self.roi = 0   
        if not self.roi and self.roiCheckBox.checkState():
            self.roi = pg.RectROI([self.roiX,  self.roiY], [self.roiW, self.roiH], maxBounds=QtCore.QRectF(0, 0, self.dimx, self.dimy), pen=(3, 10), scaleSnap=True, translateSnap=True)
            self.roi.sigRegionChanged.connect(self.update)
            self.p1.addItem(self.roi)
            self.p2.setXLink(None)
            self.p2.setYLink(None)
            self.roiLabel.setVisible(True)
            if self.roiW > self.roiH:
                self.p2.setRange(xRange=[0, self.roiW], yRange=[(self.roiH - self.roiW)/2, (self.roiH + self.roiW)/2])
            else:
                self.p2.setRange(xRange=[(self.roiW - self.roiH)/2, (self.roiW + self.roiH)/2], yRange=[0, self.roiH])
        else:
            self.p1.removeItem(self.roi)
            self.roi = 0
            self.p2.setXLink(self.p1.vb)
            self.p2.setYLink(self.p1.vb)
            self.roiLabel.setVisible(False)
            self.scaleBar2.sizeChanged(self.dimx, self.dimy)
        self.update()
        
        
    def roiChanged(self):
        if self.roiCheckBox.checkState():
            self.roiX, self.roiY = self.roi.pos()
            self.roiW, self.roiH = self.roi.size()
            self.roiLabel.setText("<font color='#00ff00'>ROI: (%d, %d) (%d, %d)</font>" % (self.roiX, self.roiY, self.roiW, self.roiH))
            self.scaleBar2.sizeChanged(self.roiW, self.roiH)
            self.scaleBar2.setAuto()
        else:
            #self.roiX, self.roiY = (0, 0)
            #self.roiW, self.roiH = (self.dimx, self.dimy)
            self.p2.setRange(xRange=[0, self.dimx], yRange=[0, self.dimy])
            
        

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
                self.cminSlider.setValue(0)
                self.cmaxSlider.setValue(np.max(self.images))
                self.enableLevels(False)
            else:
                self.enableLevels(True)
            self.update()
            
            
    def cminSliderChanged(self, value):
        self.cminSpinBox.setValue(value)
        self.im1.setLevels([self.cminSlider.value(), self.cmaxSlider.value()])
        if not self.trackingCheckBox.checkState():
            self.im2.setLevels([self.cminSlider.value(), self.cmaxSlider.value()])
        
    def cminSpinBoxChanged(self, value):
        self.cminSlider.setValue(value)
        
    def cmaxSliderChanged(self, value):
        self.cmaxSpinBox.setValue(value)
        self.im1.setLevels([self.cminSlider.value(), self.cmaxSlider.value()])
        if not self.trackingCheckBox.checkState():
            self.im2.setLevels([self.cminSlider.value(), self.cmaxSlider.value()])
        
    def cmaxSpinBoxChanged(self, value):
        self.cmaxSlider.setValue(value)
        

    def selectFilesDialog(self):
        options = QtWidgets.QFileDialog.DontUseNativeDialog 
        self.files, _ = QtWidgets.QFileDialog.getOpenFileNames(self, 'Select Files...', self.dir, ';;'.join(self.filterList), self.filterList[self.selectedFilter], options=options) # 'All Files (*)'
        if self.files:
            extension = os.path.splitext(self.files[0])[1]
            if extension == '.tdms':
                self.selectedFilter = 0
            if extension == '.tif':
                self.selectedFilter = 1
            if extension == '.mp4':
                self.selectedFilter = 2
            
        
    def selectFiles(self):
        
        self.selectFilesDialog()
        
        if self.files:
            self.fileList = []
            self.fileListWidget.clear()
            for file in self.files:
                if fnmatch.fnmatch(file,'*_movie.tdms') or fnmatch.fnmatch(file,'*_video.tdms') or fnmatch.fnmatch(file,'*.tif') or fnmatch.fnmatch(file,'*.mp4'):
                    self.fileList.append(file)
                    item = QtGui.QListWidgetItem(os.path.basename(file))
                    item.setToolTip(file)
                    self.fileListWidget.addItem(item) # self.fileListWidget.addItem(os.path.basename(file))  
                
            self.displayedItem = self.fileListWidget.item(0)
            self.displayedItem.setIcon(self.displayedIcon)
            self.displayedItemChanged(0)
            #self.frameSlider.setValue(0) # Here, self.update() is called
            #self.frameSlider.setMaximum(self.frames-1)
            self.setEnabled(True)
            
            # Connect mouseMoved events
            self.p1.scene().sigMouseMoved.connect(self.mouseMoved)   
            self.p2.getViewBox().scene().sigMouseMoved.connect(self.mouseMoved)
        
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
            if os.path.isfile(self.dir + '/' + self.protocolFile):
                self.infoLabel.setText(self.infoLabel.text() + '<br><br>' + '<a href=\"file:///' + self.dir + '/' + self.protocolFile + '\">Edit Protocol File</a>')
                self.infoLabel.setOpenExternalLinks(True)
            else:
                self.infoLabel.setText(self.infoLabel.text() + '<br><br>'  + '<span style=\"color:#ff0000;\">No Protocol File Found</span>')
               
            
    def appendFiles(self):
        if not self.fileList:
            self.selectFiles()
        else:
            self.selectFilesDialog()
            if self.files:
                for file in self.files:
                    if fnmatch.fnmatch(file, '*_movie.tdms') or fnmatch.fnmatch(file, '*_video.tdms') or fnmatch.fnmatch(file, '*.tif') or fnmatch.fnmatch(file,'*.mp4'):
                        self.fileList.append(file) 
                        item = QtGui.QListWidgetItem(os.path.basename(file))
                        item.setToolTip(file)
                        self.fileListWidget.addItem(item) # self.fileListWidget.addItem(os.path.basename(file))
                
                
    def removeFiles(self):
        for item in self.fileListWidget.selectedItems():
            if item == self.displayedItem:
                self.clearGraphs()
            del self.fileList[self.fileListWidget.row(item)]
            self.fileListWidget.takeItem(self.fileListWidget.row(item))

        if not self.fileList:
            self.clearGraphs()
            self.infoLabel.clear()
            self.cminSlider.setValue(0)
            self.cmaxSlider.setValue(0)
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
            self.infoLabel.setText('Dimensions: ' + str(self.dimx) + ' x ' + str(self.dimy) + ' x ' + str(self.frames) + '<br>' + 'Binning: ' + str(self.binning) + '<br>' + 'Exposure: ' + str(self.exposure) + ' s')
        if extension == '.tif':
            self.images = self.loadTIFFStack(file)
            self.infoLabel.setText('Dimensions: ' + str(self.dimx) + ' x ' + str(self.dimy) + ' x ' + str(self.frames))
        if extension == '.mp4':
            self.images = self.loadMP4Video(file)
            self.infoLabel.setText('Dimensions: ' + str(self.dimx) + ' x ' + str(self.dimy) + ' x ' + str(self.frames))
        
        if self.roiCheckBox.checkState():
            self.roiCheckBoxChanged()
        
        if self.maskCheckBox.checkState():
            self.maskCheckBoxChanged()
            
        self.meanSeriesImage = np.mean(self.images,axis=(0)) # image series mean for background subtraction
        
        cmaxmax = np.max(self.images) 
        self.cminSlider.setMaximum(cmaxmax)
        self.cminSpinBox.setMaximum(cmaxmax)
        self.cmaxSlider.setMaximum(cmaxmax)
        self.cmaxSpinBox.setMaximum(cmaxmax)
        
        #if not self.exportVideo:
        if self.scalingComboBox.currentIndex() == 0:
            self.cminSlider.setValue(0)
            self.cmaxSlider.setValue(cmaxmax)
        
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
        self.scaleBar1.sizeChanged(self.dimx, self.dimy)
        
        if not self.roiCheckBox.checkState():
            self.p2.setRange(xRange=[0, self.dimx], yRange=[0, self.dimy])
            self.scaleBar2.sizeChanged(self.dimx, self.dimy)
        else:
            self.roiChanged()
                     
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
        self.dimy = images.shape[1]
        self.dimx = images.shape[2]
        return images        
    
    def loadMP4Video(self, file):
        video = imageio.get_reader(file)
        self.dimx = video.get_meta_data()['size'][0]
        self.dimy = video.get_meta_data()['size'][1]
        self.frames = video.get_length()
        images = np.stack([video.get_data(i)[:,:,0] for i in range(self.frames)]) 
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
        processedFrames = 0
        totalFrames = self.images.shape[0]*len(self.fileList) # estimate the total number of frames from the first file
       
        for f, file in enumerate(self.fileList):
            self.spots = pd.DataFrame()
            if self.fileListWidget.row(self.displayedItem) == 0 and f == 0:
                pass
            else:
                self.fileDoubleClicked(self.fileListWidget.item(f))
            self.statusBar.showMessage('Feature Detection... Processing: ' + os.path.basename(file))
            for j in range(self.images.shape[0]):
                self.frameSlider.setValue(j) # this triggers update()
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
                                      'frames': self.frames,
                                      'software_binning': self.softwareBinningSpinBox.value()}])

            if os.path.splitext(file)[1] == '.tdms':
                metadata['binning'] =  self.binning
                metadata['exposure'] =  self.exposure
            
            if self.medianCheckBox.checkState():
                metadata['median'] = self.medianSpinBox.value()
            if self.subtractMeanCheckBox.checkState():
                metadata['subtract_mean'] = self.subtractMeanCheckBox.checkState()
            if self.maskCheckBox.checkState():
                metadata['maskType'] = self.maskTypeComboBox.currentText()
                metadata['maskX'] = int(self.maskX)
                metadata['maskY'] = int(self.maskY)
                metadata['maskW'] = int(self.maskW)
                metadata['maskH'] = int(self.maskH)
            if self.roiCheckBox.checkState():
                metadata['roiX'] = int(self.roiX)
                metadata['roiY'] = int(self.roiY)
                metadata['roiW'] = int(self.roiW)
                metadata['roiH'] = int(self.roiH)
            
            metadata['method'] = self.tabWidget.tabText(self.tabIndex)
            for obj in self.tabWidget.currentWidget().findChildren(QtGui.QWidget):
                if obj.metaObject().className() == 'QSpinBox':
                    metadata[obj.objectName()] = obj.value();   
                if obj.metaObject().className() == 'QCheckBox':
                    metadata[obj.objectName()] = obj.checkState();
                     
                                
            if self.preferences.suffixLineEdit.text():
                self.exportPrefix = '_' + self.preferences.suffixLineEdit.text()
            else:
                self.exportPrefix = ''
                
            # Save protocol, metadata and features in CSV file
            if self.csv:
                file = os.path.splitext(file)[0].replace('_movie', '') + self.exportSuffix + '_features.csv'
                if os.path.isfile(self.dir + '/' + self.protocolFile):
                    info = []
                    with open(self.dir + '/' + self.protocolFile, 'r') as f:
                        for line in f:
                            if '\n' in line: 
                                info.append('#' + line)
                            else:
                                info.append('#' + line + '\n')
                    with open(file, 'w') as f:
                        for line in info:
                            f.write(line)
                    metadata.to_csv(file, mode='a')  
                else:
                    metadata.to_csv(file, mode='w')  
                    
                self.spots.to_csv(file, mode='a')
                
            # Save features and metadata in HDF5 file
            if self.hdf5:
                store = pd.HDFStore(os.path.splitext(file)[0].replace('_movie', '') + self.exportSuffix + '_features.h5', 'w')
                store.put('features', self.spots)
                store.put('metadata', metadata)
                store.close()
                
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

    
    def exportVideoButtonClicked(self):
        self.exportVideo = True
        self.setEnabled(False)
        for item in self.fileListWidget.selectedItems():
            item.setSelected(False)

        self.cancelButton.setEnabled(True)
        self.canceled = False
        self.selectFilesButton.setEnabled(False)
        self.addFilesButton.setEnabled(False)
        self.removeFilesButton.setEnabled(False)
        self.batchButton.setEnabled(False)
        self.exportImageButton.setEnabled(False)
        self.exportVideoButton.setEnabled(False)
        
        if os.path.splitext(self.fileList[0])[1] == '.tdms':
            filename = os.path.splitext(self.fileList[0])[0].replace('_movie', '') + '.mp4'
        if os.path.splitext(self.fileList[0])[1] == '.tif':
            filename = os.path.splitext(self.fileList[0])[0] + '.mp4'
        
        commands = ['FFmpeg/ffmpeg',
                    '-loglevel', 'quiet',
                    '-y',  # overwrite output file if it exists
                    '-f', 'image2pipe',
                    '-vcodec', 'png',
                    '-framerate', str(self.framerateSpinBox.value()),  # frames per second
                    '-i', '-',  # The input comes from a pipe
                    '-vf', 'format=yuv420p', # same as '-pix_fmt', 'yuv420p', 
                    '-vcodec', 'libx264', # requires even width and height
                    #'-vf', 'scale=500:-2', 
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
                    w = int(self.dimx)
                    h = int(self.dimy)
                else:
                    exporter = pg.exporters.ImageExporter(self.im2)
                    if self.roiCheckBox.checkState():
                        w = int(self.roiW)
                        h = int(self.roiH)
                    else:
                        w = int(self.dimx)
                        h = int(self.dimy)
                
                exporter.params.param('width').setValue(w, blockSignal=exporter.widthChanged)
                exporter.params.param('height').setValue(h, blockSignal=exporter.heightChanged)
                
                # drop 1 pixel if width or height is not a even number (libx264 requires even width and height) 
                if w % 2 != 0:
                    w -= 1
                if h % 2 != 0:
                    h -= 1

                buffer = QtCore.QBuffer()
                buffer.open(QtCore.QIODevice.ReadWrite)
                qimage = exporter.export(toBytes=True)
                qimage.copy(QtCore.QRect(0,0, w, h)).save(buffer, 'PNG') # get image with new width and height
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
        self.exportImageButton.setEnabled(True)
        self.exportVideoButton.setEnabled(True)
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
     
    def exportImageButtonClicked(self):
        if self.exportViewComboBox.currentIndex() == 0: 
            exporter = pg.exporters.ImageExporter(self.im1)
            w = int(self.dimx)
            h = int(self.dimy)
        else:
            exporter = pg.exporters.ImageExporter(self.im2)
            if self.roiCheckBox.checkState():
                w = int(self.roiW)
                h = int(self.roiH)
            else:
                w = int(self.dimx)
                h = int(self.dimy)
        
        
        exporter.params.param('width').setValue(w, blockSignal=exporter.widthChanged)
        exporter.params.param('height').setValue(h, blockSignal=exporter.heightChanged)
                    
        if os.path.splitext(self.fileList[0])[1] == '.tdms':
            filename = os.path.splitext(self.fileList[0])[0].replace('_movie', '') + '_Frame_' + str(self.frameSlider.value()) + '.png'
        if os.path.splitext(self.fileList[0])[1] == '.tif':
            filename = os.path.splitext(self.fileList[0])[0] + '_Frame_' + str(self.frameSlider.value()) + '.png'
        
        exporter.export(filename) 
        
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
        self.settings.setValue('SelectedFilter', self.selectedFilter)
        self.settings.setValue('Pre-Processing/softwareBinning', self.softwareBinningSpinBox.value())
        self.settings.setValue('Pre-Processing/medianState', self.medianCheckBox.checkState())
        self.settings.setValue('Pre-Processing/subtractMeanState', self.subtractMeanCheckBox.checkState())
        self.settings.setValue('Pre-Processing/medianValue', self.medianSpinBox.value())
        self.settings.setValue('Pre-Processing/maskState', self.maskCheckBox.checkState())
        self.settings.setValue('Pre-Processing/maskType', self.maskTypeComboBox.currentIndex())
        self.settings.setValue('Pre-Processing/maskX', int(self.maskX))
        self.settings.setValue('Pre-Processing/maskY', int(self.maskY))
        self.settings.setValue('Pre-Processing/maskW', int(self.maskW))
        self.settings.setValue('Pre-Processing/maskH', int(self.maskH))
        self.settings.setValue('Pre-Processing/roiState', self.roiCheckBox.checkState())
        self.settings.setValue('Pre-Processing/roiX', int(self.roiX))
        self.settings.setValue('Pre-Processing/roiY', int(self.roiY))
        self.settings.setValue('Pre-Processing/roiW', int(self.roiW))
        self.settings.setValue('Pre-Processing/roiH', int(self.roiH))
        self.settings.setValue('Preferences/HDF5', self.hdf5)
        self.settings.setValue('Preferences/CSV', self.csv)
        self.settings.setValue('Preferences/protocolFile', self.protocolFile)
        self.settings.setValue('Preferences/exportSuffix', self.exportSuffix)
        self.settings.setValue('Video/exportTypeComboBox', self.exportTypeComboBox.currentIndex())
        self.settings.setValue('Video/exportViewComboBox', self.exportViewComboBox.currentIndex())
     
    
        self.scaleBar1.saveSettings('ScaleBar1', self.settings)   
        self.settings.setValue('ScaleBar1/State', self.scaleBar1CheckBox.checkState())
        
        self.scaleBar2.saveSettings('ScaleBar2', self.settings)   
        self.settings.setValue('ScaleBar2/State', self.scaleBar1CheckBox.checkState())

        
        for tabCount in range(self.tabWidget.count()):
            tab = self.tabWidget.widget(tabCount);
            for obj in tab.findChildren(QtGui.QWidget):
                if obj.metaObject().className() == 'QSpinBox':
                    self.settings.setValue('Tab' + str(tabCount + 1) + '/' + obj.objectName(), str(obj.value()))
                if obj.metaObject().className() == 'QCheckBox':
                    self.settings.setValue('Tab' + str(tabCount + 1) + '/' + obj.objectName(), str(obj.checkState()))
             
        
    def restoreSettings(self):
        
        self.settings = QSettings(QSettings.IniFormat, QSettings.UserScope, "TrackerLab", "Settings") # Open 'Settings.ini' 
        try: 
            #self.settings = QSettings('TrackerLab.ini', QSettings.IniFormat) # Opens 'TrackerLab.ini' 
            for tabCount in range(self.tabWidget.count()):
                tab = self.tabWidget.widget(tabCount);
                for obj in tab.findChildren(QtGui.QWidget):
                    if obj.metaObject().className() == 'QSpinBox':
                        obj.setValue(int(self.settings.value('Tab' + str(tabCount + 1) + '/' + obj.objectName())))
                    if obj.metaObject().className() == 'QCheckBox':
                        obj.setCheckState(int(self.settings.value('Tab' + str(tabCount + 1) + '/' + obj.objectName())))
            
            self.dir = self.settings.value('Dir', '.')
            self.selectedFilter = int(self.settings.value('SelectedFilter', '0'))
            self.trackingCheckBox.setCheckState(int(self.settings.value('TrackingState', '2')))
            self.tabWidget.setCurrentIndex(int(self.settings.value('TabIndex', '0'))) 
            self.softwareBinningSpinBox.setValue(int(self.settings.value('Pre-Processing/softwareBinning', '1')))
            self.subtractMeanCheckBox.setCheckState(int(self.settings.value('Pre-Processing/subtractMeanState', '0')))
            self.medianCheckBox.setCheckState(int(self.settings.value('Pre-Processing/medianState', '0')))
            self.medianSpinBox.setValue(int(self.settings.value('Pre-Processing/medianValue', '2'))) 
            self.maskCheckBox.setCheckState(int(self.settings.value('Pre-Processing/maskState', '0')))
            self.maskTypeComboBox.setCurrentIndex(int(self.settings.value('Pre-Processing/maskType', '0'))) 
            self.maskX = int(self.settings.value('Pre-Processing/maskX', '0'))  
            self.maskY = int(self.settings.value('Pre-Processing/maskY', '0'))  
            self.maskW = int(self.settings.value('Pre-Processing/maskW', '100'))
            self.maskH = int(self.settings.value('Pre-Processing/maskH', '100'))
            self.roiCheckBox.setCheckState(int(self.settings.value('Pre-Processing/roiState', '0')))
            self.roiX = int(self.settings.value('Pre-Processing/roiX', '0'))  
            self.roiY = int(self.settings.value('Pre-Processing/roiY', '0'))  
            self.roiW = int(self.settings.value('Pre-Processing/roiW', '100'))
            self.roiH = int(self.settings.value('Pre-Processing/roiH', '100'))
        
            self.hdf5 = int(self.settings.value('Preferences/HDF5', '1'))
            self.csv = int(self.settings.value('Preferences/CSV', '0'))
            self.preferences.radioButtonHDF5.setChecked(self.hdf5)
            self.preferences.radioButtonCSV.setChecked(self.csv)
            
            self.protocolFile = self.settings.value('Preferences/protocolFile', 'Protocol.txt')
            self.preferences.protocolFileLineEdit.setText(self.protocolFile)
            self.exportSuffix = self.settings.value('Preferences/exportSuffix', '')
            self.preferences.suffixLineEdit.setText(self.exportSuffix) 
            
            self.exportTypeComboBox.setCurrentIndex(int(self.settings.value('Video/exportTypeComboBox', '0')))
            self.exportViewComboBox.setCurrentIndex(int(self.settings.value('Video/exportViewComboBox', '0')))
            
            self.scaleBar1.restoreSettings('ScaleBar1', self.settings)
            self.scaleBar1CheckBox.setCheckState(int(self.settings.value('ScaleBar1/State', '0')))
            self.scaleBar1.setVisible(self.scaleBar1CheckBox.checkState())
            
            self.scaleBar2.restoreSettings('ScaleBar2', self.settings)
            self.scaleBar2CheckBox.setCheckState(int(self.settings.value('ScaleBar2/State', '0')))
            self.scaleBar2.setVisible(self.scaleBar2CheckBox.checkState())

            return 0
            
        except:
            self.settings.remove('') # Clear the Settings.ini file
            self.dir = '.'
            self.selectedFilter = 0
            self.maskX = 0
            self.maskY = 0
            self.maskW = 100
            self.maskH = 100
            self.roiX = 0
            self.roiY = 0
            self.roiW = 100
            self.roiH = 100
            self.csv = 1
            self.hdf5 = 0
            self.exportSuffix = ''
            self.protocolFile = 'Protocol.txt'
            return 1
            
        
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
        self.maskTypeComboBox.setEnabled(state)
        self.enableLevels(state) 
        self.batchButton.setEnabled(state)
        self.preprocessingFrame.setEnabled(state)
        self.exportImageButton.setEnabled(state)
        if self.ffmpeg:
            self.exportFrame.setEnabled(state)
            self.exportVideoButton.setEnabled(state)
        if self.exportTypeComboBox.currentIndex() == 1:
            self.startFrameSpinBox.setEnabled(False)
            self.endFrameSpinBox.setEnabled(False)
        if self.trackingCheckBox.checkState:
            self.trackingCheckBox.setEnabled(state)
        self.tabWidget.setEnabled(state)
        self.removeFilesButton.setEnabled(state)
        self.scaleBar1CheckBox.setEnabled(state)
        self.scaleBar1Button.setEnabled(state)
        self.scaleBar2CheckBox.setEnabled(state)
        self.scaleBar2Button.setEnabled(state)


    def enableLevels(self, state): 
       self.cminSlider.setEnabled(state)  
       self.cminSpinBox.setEnabled(state) 
       self.cmaxSlider.setEnabled(state)  
       self.cmaxSpinBox.setEnabled(state) 
      
    def showPreferences(self):
        if self.preferences.exec_() == QtGui.QDialog.Accepted:
            self.hdf5 = self.preferences.radioButtonHDF5.isChecked()
            self.csv = self.preferences.radioButtonCSV.isChecked()
            self.exportSuffix = self.preferences.suffixLineEdit.text()
            self.protocolFile = self.preferences.protocolFileLineEdit.text()
        else: # Rejected 
            self.preferences.radioButtonHDF5.setChecked(self.hdf5)
            self.preferences.radioButtonCSV.setChecked(self.csv)
            self.preferences.suffixLineEdit.setText(self.exportSuffix)
            self.preferences.protocolFileLineEdit.setText(self.protocolFile)
            
    
    def showScaleBar1Settings(self):
        self.scaleBar1.showSettingsDialog()
        
    #def showScaleBar2Settings(self):
    #    self.scaleBar2Settings.show() 
        
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
    





        
        
        
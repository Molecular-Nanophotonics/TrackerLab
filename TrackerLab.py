import sys
from PyQt5 import QtWidgets
from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import QMainWindow, QWidget, QApplication

from PyQt5.uic import loadUi

import pyqtgraph as pg
from pyqtgraph import QtCore, QtGui

import numpy as np

import pandas as pd
import skimage
from skimage import io
from skimage import morphology      
from skimage.feature import blob_log, blob_dog
from skimage.util import invert

from scipy import ndimage
import os, fnmatch

from nptdms import TdmsFile

class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        
        loadUi('TrackerLab.ui', self)
        
        self.settings = QSettings('TrackerLab.ini', QSettings.IniFormat)
        self.dir = self.settings.value('dir', '.')
        
        self.openFilesButton.clicked.connect(self.openFilesDialog)
        self.frameSlider.valueChanged.connect(self.frameSliderChanged)   
        self.frameSpinBox.valueChanged.connect(self.frameSpinBoxChanged)  
        self.fileComboBox.currentIndexChanged.connect(self.fileComboBoxChanged) 
      
        self.batchButton.clicked.connect(self.batchButtonClicked)
        self.abortButton.clicked.connect(self.abortButtonClicked)
        self.abort = False
 
        self.settings = QSettings('TrackerLab.ini', QSettings.IniFormat)
        self.dir = self.settings.value('Dir', '.')


        self.medianCheckBox.setCheckState(int(self.settings.value('Pre-Processing/MedianState', '0')))
        self.medianSpinBox.setValue(int(self.settings.value('Pre-Processing/MedianValue', '2')))  
        self.medianCheckBox.stateChanged.connect(self.update)  
        self.medianSpinBox.valueChanged.connect(self.update)
        
        self.maskCheckBox.setCheckState(int(self.settings.value('Pre-Processing/MaskState', '0')))
        self.maskSpinBox.setValue(int(self.settings.value('Pre-Processing/MaskValue', '25')))  
        self.maskCheckBox.stateChanged.connect(self.update) 
        self.maskSpinBox.valueChanged.connect(self.maskChanged)
        self.mask = np.array([])
        
        self.trackingCheckBox.stateChanged.connect(self.trackingCheckBoxChanged)
        
        self.tabWidget.currentChanged.connect(self.update) 
        self.tabIndex = 0
        
        self.tab1Threshold = self.settings.value('Tab1/Threshold', '1000')
        self.tab1MinArea = self.settings.value('Tab1/MinArea', '10')
        self.tab1MaxArea = self.settings.value('Tab1/MaxArea', '250')
        self.tab1ThresholdSpinBox.valueChanged.connect(self.update)  
        self.tab1MinAreaSpinBox.valueChanged.connect(self.update)  
        self.tab1MaxAreaSpinBox.valueChanged.connect(self.update)  
        
        self.tab1InvertCheckBox.stateChanged.connect(self.update) 
        
        self.tab2Threshold = self.settings.value('Tab2/Threshold', '0.1')
        self.tab2MaxSigma = self.settings.value('Tab2/MaxSigma', '10')
        self.tab2ThresholdSpinBox.valueChanged.connect(self.update)  
        self.tab2MaxSigmaSpinBox.valueChanged.connect(self.update)    
        
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 0.75)
        
        graphicsLayout = pg.GraphicsLayoutWidget()
        self.layout.addWidget(graphicsLayout)
        
        '''
        self.p = graphicsLayout.addPlot()
        self.p.setAspectLocked(True)
        self.img = pg.ImageItem()
        self.p.addItem(self.img)
        '''
        
        self.p = graphicsLayout.addPlot(row=1, col=1)
        self.p.showAxis('top')
        self.p.showAxis('right')
        self.p.getAxis('top').setStyle(showValues=False)
        self.p.getAxis('right').setStyle(showValues=False)
        self.p.getAxis('top').setHeight(10)
        self.p.getAxis('right').setWidth(15)
        #self.p.setLimits(xMin=0, yMin=0)
        self.p.setAspectLocked(True)
        self.im1 = pg.ImageItem()
        self.p.addItem(self.im1)
        self.p.getViewBox().invertY(True)
        
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
        
        self.p2.setXLink(self.p.vb)
        self.p2.setYLink(self.p.vb)

        self.sp = pg.ScatterPlotItem(pen=pg.mkPen('r', width=2), brush=pg.mkBrush(None), pxMode=False)
        self.p2.addItem(self.sp)
    
        #self.vb = self.p.vb
        #self.p.scene().sigMouseMoved.connect(self.mouseMoved)  
                
        self.p.scene().sigMouseMoved.connect(self.mouseMoved)   
        self.p2.getViewBox().scene().sigMouseMoved.connect(self.mouseMoved) 

        #self.vb.scene().sigMouseMoved.connect(self.mouseMoved)   
        #self.vb2.scene().sigMouseMoved.connect(self.mouseMoved) 
        
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
        
        self.setEnabled(False)
        self.abortButton.setEnabled(False)
        
        #pg.SignalProxy(self.p.scene().sigMouseMoved, rateLimit=60, slot=self.mouseMoved)
        #pg.SignalProxy(self.p2.scene().sigMouseMoved, rateLimit=60, slot=self.mouseMoved)
        
    def mouseMoved(self, e):
        if self.p.vb.sceneBoundingRect().contains(e):
            mousePoint = self.p.vb.mapSceneToView(e)
            x = int(mousePoint.x())
            y = int(mousePoint.y()) 
            if x > 0 and x < self.dimx and y > 0 and y < self.dimy:
                self.infoLabel.setText("x = %d\ty = %d\t[%d]" % (x, y, self.images[self.frameSlider.value(), x ,y]))
                
        if self.p2.vb.sceneBoundingRect().contains(e):
            mousePoint = self.p2.vb.mapSceneToView(e)  
            x = int(mousePoint.x())
            y = int(mousePoint.y()) 
            if x > 0 and x < self.dimx and y > 0 and y < self.dimy:
                self.infoLabel.setText("x = %d\ty = %d\t[%d]" % (x, y, self.processedImage[x, y]))
                
            #vLine.setPos(mousePoint.x())
            #hLine.setPos(mousePoint.y())
    
        
    def update(self):
            
        self.tabIndex =  self.tabWidget.currentIndex()
        
        self.tab1Threshold = self.tab1ThresholdSpinBox.value()
        self.tab1MinArea = self.tab1MinAreaSpinBox.value()
        self.tab1MaxArea = self.tab1MaxAreaSpinBox.value()
        
        self.tab2Threshold = self.tab2ThresholdSpinBox.value()
        self.tab2MaxSigma = self.tab2MaxSigmaSpinBox.value()
        
        self.im1.setImage(self.images[self.frameSlider.value()])        

        self.processedImage = self.images[self.frameSlider.value()]
        
        # Image Pre-Processing 
        if self.medianCheckBox.checkState():
            self.processedImage = ndimage.median_filter(self.processedImage, self.medianSpinBox.value())
            
        if self.maskCheckBox.checkState():
            if not self.mask.shape[0] == self.dimx or not self.mask.shape[1] == self.dimy:
                self.maskChanged()
            self.processedImage = self.mask*self.processedImage
        
        if self.trackingCheckBox.checkState():
            # Tracking
            if self.tabIndex == 0:
                spots = self.findSpots1(self.frameSlider.value())   
            if self.tabIndex == 1:
                spots = self.findSpots2(self.frameSlider.value())
                
            self.im2.setImage(self.processedImage) 
                  
            if spots.size > 0:
                self.sp.setData(x=spots.x.tolist(), y=spots.y.tolist(), size=2*np.sqrt(np.array(spots.area.tolist())/np.pi))
                self.numberOfSpots.setText(str(spots.shape[0]))
            else:
                self.sp.setData(x=None, y=None)
        else:
            self.tabWidget.setEnabled(False)
            self.im2.setImage(self.processedImage)
            self.sp.setData(x=None, y=None)
        
        if self.batch:
            self.spots = self.spots.append(spots)
            

            
        #self.sp.setData(x=spots.x.tolist(), y=spots.y.tolist(), size=10)
     
        
     # Maximum Tracking     
    def findSpots1(self, i):
        spots = pd.DataFrame()
        self.intensityImage = self.processedImage
        self.processedImage = self.processedImage > self.tab1Threshold*self.processedImage.max()
        if self.tab1InvertCheckBox.checkState():
            self.processedImage = invert(self.processedImage)
        labelImage = skimage.measure.label(self.processedImage)
        for region in skimage.measure.regionprops(label_image=labelImage, intensity_image=self.intensityImage):
            if region.area < self.tab1MinArea or region.area > self.tab1MaxArea: # do not add spot
                continue
            spots = spots.append([{'x': region.centroid[0],
                                   'y': region.centroid[1],
                                   'area': region.area,
                                   'max_intensity': region.max_intensity,
                                   'frame': i,}])    
        return spots  

    # Difference of Gaussians
    def findSpots2(self, i):
        spots = blob_dog(self.processedImage/self.processedImage.max(), max_sigma=self.tab2MaxSigma, threshold=self.tab2Threshold)
        if spots.size > 0:
            spots[:, 2] = np.pi*(spots[:, 2]*np.sqrt(2))**2 # area
            return pd.DataFrame(np.transpose([spots[:,0], spots[:,1], spots[:,2], i*np.ones(spots.shape[0])]), columns=['x', 'y', 'area', 'frame'])   
        else:
            return pd.DataFrame()
          
    #def trackingSpinBoxChanged(self):
        
    def maskChanged(self):
        x0 = int(self.dimx/2)
        y0 = int(self.dimy/2)
        diameter = 2*self.maskSpinBox.value()
        xx, yy= np.meshgrid(np.arange(0, self.dimx, 1), np.arange(0, self.dimy, 1))
        self.mask = (((xx - x0)**2 + (yy - y0)**2) < (diameter/2)**2).astype(int)
        self.update()
        
        
    def editImage(self, i):
        image = self.images[i] > self.tab1Threshold
        if self.tab1InvertCheckBox.checkState():
            return invert(image)
        else:
            return image
    
        
    def frameSliderChanged(self, value):
        self.frameSpinBox.setValue(value)
        self.update()
    
        
    def frameSpinBoxChanged(self, value):
        self.frameSlider.setValue(value)

    def fileComboBoxChanged(self, value):
        
        if value >= 0:
            self.statusBar.showMessage('Loading File...')
            file = self.imageFiles[value]
            extension = os.path.splitext(file)[1]
            if extension == ".tdms":
                self.images = self.loadTDMSImages(file)
            if extension == ".tif":
                self.images = self.loadTIFFStack(file)
            self.update()
            self.frameSlider.setValue(0) # Here, self.update() is called again
            self.frameSlider.setMaximum(self.frames-1)
            self.frameSpinBox.setMaximum(self.frames-1)
            #self.p.setLimits(xMax=self.dimx, yMax=self.dimy)
            self.p.setRange(xRange=[0, self.dimx], yRange=[0, self.dimy])
            #self.p2.setLimits(xMax=self.dimx, yMax=self.dimy)
            self.p2.setRange(xRange=[0, self.dimx], yRange=[0, self.dimy])
            
            self.statusBar.showMessage('Ready')

            
    def openFilesDialog(self):
        self.files, _ =  QtWidgets.QFileDialog.getOpenFileNames(self, 'Open Files...', self.dir, 'All Files (*)')
        if self.files:
            self.imageFiles = []
            self.fileComboBox.clear()
            for file in self.files:
                if fnmatch.fnmatch(file,'*_movie.tdms') or fnmatch.fnmatch(file,'*.tif'):
                    self.imageFiles.append(file)
                    self.fileComboBox.addItem(os.path.basename(file))       
            self.frameSlider.setValue(0) # Here, self.update() is called
            self.frameSlider.setMaximum(self.frames-1)
            self.propertiesLabel.setText(str(self.dimx) + ' x ' + str(self.dimy))
            self.setEnabled(True)
            self.dir = os.path.dirname(self.files[0])
        
                    
    def loadTDMSImages(self, file):
        tdms_file = TdmsFile(file)
        p = tdms_file.object().properties   
        self.dimx = int(p['dimx'])  
        self.dimy = int(p['dimy'])
        self.frames = int(p['dimz'])
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
        self.batch = True
        self.openFilesButton.setEnabled(False)
        self.abortButton.setEnabled(True)
        processedFrames = 0
        totalFrames = self.images.shape[0]*self.fileComboBox.count() # estimate the total number of frames from the first file
        for i, imageFile in enumerate(self.imageFiles):
            self.spots = pd.DataFrame()
            self.fileComboBox.setCurrentIndex(i) # Here, the fileComboBoxChanged() event is called
            self.statusBar.showMessage('Batch...')
            for j in range(self.images.shape[0]):
                self.frameSlider.setValue(j) # Here, the frameSilderChanged() event is called
                processedFrames += 1
                self.progressBar.setValue(processedFrames/totalFrames*100)
                QtWidgets.QApplication.processEvents()
                if self.abort:
                    self.progressBar.setValue(0)
                    self.statusBar.showMessage('Ready')
                    break
            self.spots.to_pickle(os.path.splitext(imageFile)[0].replace('_movie', '') + '_spots.pkl')
            if self.abort:
                break
            
        self.setEnabled(True)
        self.openFilesButton.setEnabled(True)
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
        self.update()
        
        
    def closeEvent(self, e):
        # save the settings in the TrackerLab.ini file
        self.settings.setValue('Dir', self.dir)
        self.settings.setValue('Pre-Processing/MedianState', self.medianCheckBox.checkState())
        self.settings.setValue('Pre-Processing/MedianValue', self.medianSpinBox.value())
        self.settings.setValue('Pre-Processing/MaskState', self.maskCheckBox.checkState())
        self.settings.setValue('Pre-Processing/MaskValue', self.maskSpinBox.value())
        self.settings.setValue('Tab1/Threshold', self.tab1Threshold)
        self.settings.setValue('Tab1/MinArea', self.tab1MinArea)
        self.settings.setValue('Tab1/MaxArea', self.tab1MaxArea)
        self.settings.setValue('Tab1/Invert', self.tab1InvertCheckBox.checkState())
        self.settings.setValue('Tab2/Threshold', self.tab2Threshold)
        self.settings.setValue('Tab2/MaxSigma', self.tab2MaxSigma)
        e.accept()
        
        
    def setEnabled(self, state):
        self.fileComboBox.setEnabled(state)
        self.frameSlider.setEnabled(state)
        self.frameSpinBox.setEnabled(state)
        self.batchButton.setEnabled(state)
        self.preprocessingFrame.setEnabled(state)
        self.trackingCheckBox.setEnabled(state)
        self.tabWidget.setEnabled(state)
        
        
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec_())
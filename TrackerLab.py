import sys
from PyQt5 import QtWidgets
from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import QMainWindow, QWidget, QApplication, QDialog, QMessageBox

from PyQt5.uic import loadUi

import pyqtgraph as pg
from pyqtgraph import QtCore, QtGui
import inspect

from matplotlib import cm # for colormaps

import numpy as np

import pandas as pd
import skimage
#from skimage import io
from skimage import morphology      
from skimage.feature import blob_log, blob_dog
from skimage.util import invert

from scipy import ndimage
import os, fnmatch, glob

from nptdms import TdmsFile
import pickle

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

        # restore setting from TrackerLab.ini file
        self.settings = QSettings('TrackerLab.ini', QSettings.IniFormat)
        self.restoreSettings() 
        
        self.openFilesButton.clicked.connect(self.openFilesDialog)
        self.frameSlider.valueChanged.connect(self.frameSliderChanged)   
        self.frameSpinBox.valueChanged.connect(self.frameSpinBoxChanged)  
        self.fileComboBox.currentIndexChanged.connect(self.fileComboBoxChanged) 
      
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
        self.trackingTabWidget.currentChanged.connect(self.update) 
        self.tabIndex = 0
        
        self.tab1ThresholdSpinBox.valueChanged.connect(self.update)  
        self.tab1MinAreaSpinBox.valueChanged.connect(self.update)  
        self.tab1MaxAreaSpinBox.valueChanged.connect(self.update)          
        self.tab1InvertCheckBox.stateChanged.connect(self.update) 
        self.tab1MaxFeaturesSpinBox.valueChanged.connect(self.update) 
        
        self.tab2ThresholdSpinBox.valueChanged.connect(self.update)  
        self.tab2MaxSigmaSpinBox.valueChanged.connect(self.update)    
     
        self.actionOpen.triggered.connect(self.openFilesDialog)
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

        self.sp = pg.ScatterPlotItem(pen=pg.mkPen('r', width=2), brush=pg.mkBrush(None), pxMode=False)
        self.p2.addItem(self.sp)
        
        #self.p = pg.PlotItem(pen=pg.mkPen('r', width=2), brush=pg.mkBrush(None), pxMode=False)
        #self.p2.addItem(self.p)
        
        #self.vb = self.p.vb
        #self.p.scene().sigMouseMoved.connect(self.mouseMoved)  
                
        self.p1.scene().sigMouseMoved.connect(self.mouseMoved)   
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
        
        # load colormaps        
        self.colormaps = []
        self.colormapComboBox.clear()
        for file in glob.glob('Colormaps/*.pkl'):
            self.colormapComboBox.addItem(os.path.splitext(os.path.basename(file))[0])
            self.colormaps.append(pickle.load(open(file, 'rb')))
               
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
        
        
    def mouseMoved(self, e):
        if self.p1.vb.sceneBoundingRect().contains(e):
            mousePoint = self.p1.vb.mapSceneToView(e)
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
            
        self.tabIndex =  self.trackingTabWidget.currentIndex()
        
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
            if self.tabIndex == 0:
                spots = self.findSpots1(self.frameSlider.value())   
                
            if self.tabIndex == 1:
                spots = self.findSpots2(self.frameSlider.value())
                
            self.im2.setImage(self.processedImage) 
                  
            if spots.size > 0:
                self.sp.setData(x=spots.x.tolist(), y=spots.y.tolist(), size=2*np.sqrt(np.array(spots.area.tolist())/np.pi))
                self.numberOfSpots.setText(str(spots.shape[0]))
            else:
                self.numberOfSpots.setText('0')
                self.sp.setData(x=None, y=None)
        else:
            self.trackingTabWidget.setEnabled(False)
            if self.scalingComboBox.currentIndex() == 0:
                self.im2.setImage(self.processedImage)
            else:
                self.im2.setImage(self.processedImage, levels=[self.lminSlider.value(), self.lmaxSlider.value()])
            self.sp.setData(x=None, y=None)
        
        if self.batch:
            self.spots = self.spots.append(spots)
            
        #self.sp.setData(x=spots.x.tolist(), y=spots.y.tolist(), size=10)
     
        
     # Maximum Tracking     
    def findSpots1(self, i): # rename to trackingTab1 ???
        spots = pd.DataFrame()
        self.intensityImage = self.processedImage
        self.processedImage = self.processedImage > self.tab1Threshold # relative threshold
        #self.processedImage = self.processedImage < self.tab1MinThreshold
        if self.tab1InvertCheckBox.checkState():
            self.processedImage = invert(self.processedImage)
        labelImage = skimage.measure.label(self.processedImage)
        regions = skimage.measure.regionprops(label_image=labelImage, intensity_image=self.intensityImage) # http://scikit-image.org/docs/dev/api/skimage.measure.html
        j = 0
        for region in regions:
            # area filter first
            if region.area < self.tab1MinArea or region.area > self.tab1MaxArea:   # do not add feature
                continue
            if j >= self.tab1MaxFeatures: # do not add feature
                continue 
            spots = spots.append([{'y': region.centroid[0], 
                                   'x': region.centroid[1],
                                   'orientation': region.orientation,
                                   'minor_axis_length': region.minor_axis_length,
                                   'major_axis_length': region.major_axis_length,
                                   'area': region.area,
                                   #'bbox': region.bbox,
                                   'max_intensity': region.max_intensity,
                                   'frame': i,}]) 
            j += 1 # feature added
        return spots  

    # Difference of Gaussians
    def findSpots2(self, i):
        spots = blob_dog(self.processedImage/self.processedImage.max(), max_sigma=self.tab2MaxSigma, threshold=self.tab2Threshold)
        if spots.size > 0:
            spots[:, 2] = np.pi*(spots[:, 2]*np.sqrt(2))**2 # area
            return pd.DataFrame(np.transpose([spots[:,0], spots[:,1], spots[:,2], i*np.ones(spots.shape[0])]), columns=['x', 'y', 'area', 'frame'])   
        else:
            return pd.DataFrame()
          
    # Janus Particle 1
        
    
    def maskChanged(self):
        x0 = self.maskXSpinBox.value() #int(self.dimx/2)
        y0 = self.maskYSpinBox.value() #int(self.dimy/2)
        diameter = 2*self.maskRadiusSpinBox.value()
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
        
        file = self.imageFiles[value]
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

            
    def openFilesDialog(self):
        self.files, _ =  QtWidgets.QFileDialog.getOpenFileNames(self, 'Open Files...', self.dir, 'TDMS Files (*.tdms);;TIFF Files (*.tif)') # 'All Files (*)'
        if self.files:
            self.imageFiles = []
            self.fileComboBox.blockSignals(True)
            self.fileComboBox.clear()
            self.fileComboBox.blockSignals(False)
            for file in self.files:
                if fnmatch.fnmatch(file,'*_movie.tdms') or fnmatch.fnmatch(file,'*.tif'):
                    self.imageFiles.append(file)
                    self.fileComboBox.addItem(os.path.basename(file))       
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
            self.update()
        
                    
    def loadTDMSImages(self, file):
        tdms_file = TdmsFile(file)
        p = tdms_file.object().properties
        self.dimx = int(p['dimx'])
        self.dimy = int(p['dimy'])
        self.binning = int(p['binning'])
        self.frames = int(p['dimz'])
        self.exposure = float(p['exposure'])
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
            if self.fileComboBox.currentIndex() == 0 and i == 0:
                self.fileComboBoxChanged(0)
            else:
                self.fileComboBox.setCurrentIndex(i)
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
                store = pd.HDFStore(os.path.splitext(imageFile)[0].replace('_movie', '') + '_spots.h5', 'w')

                store.put('spots', self.spots)
                
                # save metadata as data frame
                metadata = pd.DataFrame([{'dimx': self.dimx,
                                          'dimy': self.dimx,
                                          'binning': self.binning,
                                          'frames': self.frames,
                                          'exposure': self.exposure}])
                
                if self.medianCheckBox.checkState():
                    metadata['pp_median'] = self.medianSpinBox.value()
                if self.maskCheckBox.checkState():
                    metadata['pp_mask_x'] = self.maskXSpinBox.value()
                    metadata['pp_mask_y'] = self.maskYSpinBox.value()
                    metadata['pp_mask_r'] = self.maskRadiusSpinBox.value()
                    
                if self.tabIndex == 0:
                    metadata['tt_method'] = self.trackingTabWidget.tabText(self.tabIndex)
                    metadata['tt_threshold'] = self.tab1Threshold
                    metadata['tt_area_min'] = self.tab1MinArea
                    metadata['tt_area_max'] =  self.tab1MaxArea
                
                store.put('metadata', metadata)
                
                store.close()
                
                '''
                store.get_storer('spots').attrs.dimx = self.dimx
                store.get_storer('spots').attrs.dimy = self.dimy
                store.get_storer('spots').attrs.binning = self.binning
                store.get_storer('spots').attrs.frames = self.frames
                store.get_storer('spots').attrs.exposure = self.exposure
                
                if self.medianCheckBox.checkState():
                    store.get_storer('spots').attrs.pp_median = self.medianSpinBox.value()
                if self.maskCheckBox.checkState():
                    store.get_storer('spots').attrs.pp_mask_x = self.maskXSpinBox.value()
                    store.get_storer('spots').attrs.pp_mask_y = self.maskYSpinBox.value()
                    store.get_storer('spots').attrs.pp_mask_radius = self.maskRadiusSpinBox.value()
                    
                if self.tabIndex == 0:
                    store.get_storer('spots').attrs.t_threshold = self.tab1Threshold
                    store.get_storer('spots').attrs.t_minarea = self.tab1MinArea
                    store.get_storer('spots').attrs.t_maxarea = self.tab1MaxArea
                '''
                
            if self.csv: # save as csv file
                file = os.path.splitext(imageFile)[0].replace('_movie', '') + '_spots.csv'
                with open(file, 'w') as f:
                    f.write('# dimx,dimy,frames,binning\n')
                    f.write('# %d,%d,%d,%d\n' % (self.dimx, self.dimy, self.frames, self.binning))

                self.spots.to_csv(file, mode='a')
                
                
            '''    
            else: # save metadata 
                self.spots.to_pickle(os.path.splitext(imageFile)[0].replace('_movie', '') + '_features.pkl')
                metadata = {'dimx': self.dimx,
                            'dimy': self.dimx,
                            'binning': self.binning,
                            'frames': self.frames,
                            'exposure': self.exposure}
                # Pre-Processing
                if self.medianCheckBox.checkState():
                    metadata['pp_median'] = self.medianSpinBox.value()
                if self.maskCheckBox.checkState():
                    metadata['pp_mask_x'] = self.maskXSpinBox.value()
                    metadata['pp_mask_y'] = self.maskYSpinBox.value()
                    metadata['pp_mask_r'] = self.maskRadiusSpinBox.value()
                # Tracking
                if self.tabIndex == 0:
                    metadata['t_method'] = self.trackingTabWidget.tabText(self.tabIndex)
                    metadata['t_threshold'] = self.tab1Threshold
                    metadata['t_area_min'] = self.tab1MinArea
                    metadata['t_area_max'] =  self.tab1MaxArea
                
                with open(os.path.splitext(imageFile)[0].replace('_movie', '') + '_metadata.pkl', 'wb') as f:
                    pickle.dump(metadata, f)
        
                #f = open(os.path.splitext(imageFile)[0].replace('_movie', '') + '_metadata.csv', 'wb')
                #w = csv.writer(f, delimiter=",") #delimiter=","
                #for key, val in metadata.items():
                #    w.writerow([key, val])
   
                #df = pd.DataFrame([metadata])  
                #df.to_pickle(os.path.splitext(imageFile)[0].replace('_movie', '') + '_metadata.pkl')
            '''
            
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
            self.trackingTabWidget.setEnabled(True)
        else:
            self.trackingTabWidget.setEnabled(False)
        self.update()
        
        
    def closeEvent(self, e):
        # Save the current settings in the TrackerLab.ini file
        self.saveSettings()
        e.accept()
        
        
    def saveSettings(self):
        self.settings.setValue('Dir', self.dir)
        self.settings.setValue('TrackingTabIndex', self.trackingTabWidget.currentIndex())
        self.settings.setValue('TrackingState', self.trackingCheckBox.checkState())
        self.settings.setValue('Pre-Processing/MedianState', self.medianCheckBox.checkState())
        self.settings.setValue('Pre-Processing/MedianValue', self.medianSpinBox.value())
        self.settings.setValue('Pre-Processing/MaskState', self.maskCheckBox.checkState())
        self.settings.setValue('Pre-Processing/MaskX', self.maskXSpinBox.value())
        self.settings.setValue('Pre-Processing/MaskY', self.maskYSpinBox.value())
        self.settings.setValue('Pre-Processing/MaskRadius', self.maskRadiusSpinBox.value())
        self.settings.setValue('Tab1/Threshold', self.tab1ThresholdSpinBox.value())
        self.settings.setValue('Tab1/MinArea', self.tab1MinAreaSpinBox.value())
        self.settings.setValue('Tab1/MaxArea', self.tab1MaxAreaSpinBox.value())
        self.settings.setValue('Tab1/Invert', self.tab1InvertCheckBox.checkState())
        self.settings.setValue('Tab1/MaxFeatures', self.tab1MaxFeaturesSpinBox.value())
        self.settings.setValue('Tab2/Threshold', self.tab2ThresholdSpinBox.value())
        self.settings.setValue('Tab2/MaxSigma', self.tab2MaxSigmaSpinBox.value())
        self.settings.setValue('Settings/HDF5', self.hdf5)
        self.settings.setValue('Settings/CSV', self.csv)
        
        
    def restoreSettings(self):
        self.dir = self.settings.value('Dir', '.')
        self.trackingCheckBox.setCheckState(int(self.settings.value('TrackingState', '2')))
        self.trackingTabWidget.setCurrentIndex(int(self.settings.value('TrackingTabIndex', '0'))) 
        self.medianCheckBox.setCheckState(int(self.settings.value('Pre-Processing/MedianState', '0')))
        self.medianSpinBox.setValue(int(self.settings.value('Pre-Processing/MedianValue', '2'))) 
        self.maskCheckBox.setCheckState(int(self.settings.value('Pre-Processing/MaskState', '0')))
        self.maskXSpinBox.setValue(int(self.settings.value('Pre-Processing/MaskX', '100')))  
        self.maskYSpinBox.setValue(int(self.settings.value('Pre-Processing/MaskY', '100')))  
        self.maskRadiusSpinBox.setValue(int(self.settings.value('Pre-Processing/MaskRadius', '100')))  
        self.tab1ThresholdSpinBox.setValue(int(self.settings.value('Tab1/Threshold', '1000')))
        self.tab1MinAreaSpinBox.setValue(int(self.settings.value('Tab1/MinArea', '10')))
        self.tab1MaxAreaSpinBox.setValue(int(self.settings.value('Tab1/MaxArea', '250')))
        self.tab1MaxFeaturesSpinBox.setValue(int(self.settings.value('Tab1/MaxFeatures', '1000')))
        self.tab2ThresholdSpinBox.setValue(float(self.settings.value('Tab2/Threshold', '0.1')))
        self.tab2MaxSigmaSpinBox.setValue(int(self.settings.value('Tab2/MaxSigma', '10')))
        self.hdf5 = int(self.settings.value('Settings/HDF5', '2'))
        self.csv = int(self.settings.value('Settings/CSV', '0'))

            
    def setEnabled(self, state):
        self.fileComboBox.setEnabled(state)
        self.frameSlider.setEnabled(state)
        self.frameSpinBox.setEnabled(state)
        self.batchButton.setEnabled(state)
        self.preprocessingFrame.setEnabled(state)
        self.trackingCheckBox.setEnabled(state)
        self.trackingTabWidget.setEnabled(state)

       
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
       QMessageBox.about(self, 'About', 
                               'This is the Molecular Nanophotonics TrackerLab. '
                             + 'It is based on PyQt and the PyQtGraph libary.' + 2*'\n'
                             + 'Martin Fränzl')    
       
     
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec_())
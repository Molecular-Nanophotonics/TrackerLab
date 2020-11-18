# -*- coding: utf-8 -*-
"""
Discription: Module for Janus-paritcle Labeling. The module works with multiple thresholds to determine the orientaion of a Janus particle.
Author(s):   Nicola Andreas Söker
Date:        17/08/20
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
        #self.invertCheckBox.stateChanged.connect(self.updated.emit)
        self.maxFeaturesSpinBox.valueChanged.connect(self.updated.emit)
        self.showOverlayCheckBox.stateChanged.connect(self.updated.emit)
        self.showThresholdCheckBox.stateChanged.connect(self.updated.emit)
        self.MaxElipticitySpinBox.valueChanged.connect(self.updated.emit)
        self.SeparateClosePairsCheckBox.stateChanged.connect(self.updated.emit)
        self.MinAreaPairSpinBox.valueChanged.connect(self.updated.emit)
        self.MaxAreaPairSpinBox.valueChanged.connect(self.updated.emit)
        self.MinElipticityPairSpinBox.valueChanged.connect(self.updated.emit)
        self.Crescent_ratioSpinBox.valueChanged.connect(self.updated.emit)
        
        
    def attach(self, plot):
        self.p = plot
        self.items = []
        restoreSettings(self.settingsFile, self.widget)
        
        
    def detach(self):
        for item in self.items:
            self.p.removeItem(item) 
        saveSettings(self.settingsFile, self.widget)
        

    def findFeatures(self, frame, imageItem):
            
        threshold = self.thresholdSpinBox.value()
        MinArea = self.minAreaSpinBox.value()
        MaxArea = self.maxAreaSpinBox.value()
        MaxFeatures = self.maxFeaturesSpinBox.value()
        #invert = self.invertCheckBox.checkState()
        MaxElipticity = self.MaxElipticitySpinBox.value()
        SeparateClosePairs = self.SeparateClosePairsCheckBox.checkState()
        MinAreaPair = self.MinAreaPairSpinBox.value()
        MaxAreaPair = self.MaxAreaPairSpinBox.value()
        MinElipticityPair = self.MinElipticityPairSpinBox.value()
        Crescent_ratio = self.Crescent_ratioSpinBox.value()/100
        
        
        def Threshold(image,TH,new_value,**kwargs):
            """eats a xy grayscale image and applys threshold TH with new value. 
            ad 'both' or 'inverse' as kwargs, you can also set a new upper value"""
            kwargs.setdefault('mode', 'normal')#set default values for kwargs
            if kwargs.get('mode') == 'inverse':
                indices = image > TH #make an index list of values forfilling the condition
                image[indices] = new_value
            elif kwargs.get('mode')=='both':
                indices = image < TH
                image[indices]=0
                indices = image >= TH
                image[indices] = 1
            elif kwargs.get('mode')=='normal':
                indices = image < TH
                image[indices]=new_value
            return 
        
        def Center_of_mass(image):
            """center of mass/intensity (CoM) of a 2D graysacale image"""
            dim_x = np.shape(image)[0]
            dim_y = np.shape(image)[1]
            CoM_x = 0.
            CoM_y = 0.
            Norm = 0.
            for x in range(dim_x):
                for y in range(dim_y):
                    CoM_x += image[x][y]*(x)
                    CoM_y += image[x][y]*(y)
                    Norm += image[x][y]
            if Norm == 0:
                print('image is zero everywhere, something went wrong bevor center of mass determination')
                return
            else:
                out = np.array([CoM_x,CoM_y])/Norm # divide by the normalisation
            return out[0],out[1]
        
        def Track_single_JP(image,**kwargs):
            #kwargs.setdefault('show', 'off')#set default values for kwargs
            from copy import deepcopy
            Th_list = []
            steps = 5
            Th_list.append(threshold)
            CoMs = np.zeros((2,steps)) #[0] is particle pos, higher incides are orientaion related CoMs
            without_background_flat = deepcopy(image)
            Threshold(without_background_flat,Th_list[0],0,mode='both')
            CoMs[0][0],CoMs[1][0] = Center_of_mass(without_background_flat)
            #calc orientation of JP
            max_intensity = np.amax(image) 
            for i in range(1,steps): # a list of numbers linear distributed along min(Th of background substraction) and max intensity of particle
                image_Th = deepcopy(image)
                Th = Th_list[0]+(max_intensity - Th_list[0])/steps*i
                Threshold(image_Th,Th,0)
                CoMs[0][i],CoMs[1][i]=(Center_of_mass(image_Th))
            CoMs_rel = deepcopy(CoMs)
            CoMs_rel[1,:] -= CoMs[1,0]
            CoMs_rel[0,:] -= CoMs[0,0]
            angles = np.arctan2(CoMs_rel[1,1:],CoMs_rel[0,1:])
            trigger1 = 0
            for i in range(len(angles)):  #take care of the case where phi is near pi and therefore the mean calc goes wrong, this only works because the spread in phi is small!!
                if (angles[i] > 3/4*3.14) and trigger1 == 0:
                    trigger1 = 1
                elif (angles[i] < -3/4*3.14) and trigger1 == 0:
                    trigger1 = 2
                if (trigger1 == 1) and (angles[i]<=0):
                    angles[i] += 2*np.pi
                elif (trigger1 == 2) and (angles[i]>=0):
                    angles[i] -= 2*np.pi
            phi = np.mean(angles)
            if phi > np.pi:  ## phi ! element of [-pi,pi]
                phi += -2*np.pi
            elif phi < -np.pi:
                phi += 2*np.pi
            return CoMs[0,0],CoMs[1,0],phi
        
        def Make_separated_JP_images(x = 0, y = 0, phi = 0, image = None):
            def CreateMaskAlongAxis(h,w,x,y,angle):
                Y,X = np.ogrid[:h,:w]
                scalarProduct = np.sin(angle)*(X-x)   + np.cos(angle)*(Y-y)
                mask = scalarProduct <= 0
                return mask
            mask = CreateMaskAlongAxis(image.shape[0],image.shape[1],x,y,phi+np.pi/2)
            from copy import deepcopy
            image1 = deepcopy(image)
            image1[mask] = 0
            image2 = image - image1
            return [image1,image2]
        
        def Crescent_width(JP_image,x_JP,y_JP,Crescent_ratio):
            nbins = 10
            phi_edges = np.linspace(-np.pi, np.pi, nbins+1)
            #dphi = phi_edges[1] - phi_edges[0]
            #phi_mids = phi_edges[:-1] + dphi/2
            #i_list = np.arange(nbins)
            dimy = np.shape(JP_image)[0]
            dimx = np.shape(JP_image)[1]
            x_list = np.arange(dimx) - dimx/2
            y_list = np.arange(dimy) - dimx/2
            x_M, y_M = np.meshgrid(x_list, y_list)
            r_M = np.sqrt(x_M**2 + y_M**2)
            phi_M = np.arctan2(x_M,y_M)
            #phi_hist = np.zeros(nbins)
            mean_int_list = np.zeros(nbins)
            for i in range(nbins):
                #phi_hist[i] = np.sum( (phi_M > phi_edges[i])&(phi_M < phi_edges[i+1]) )
                mean_int_list[i] = np.mean( JP_image[(phi_M > phi_edges[i]) & (phi_M < phi_edges[i+1]) & (r_M < np.mean([dimx,dimy])/2)] )
            max_int = np.max(mean_int_list)
            #min_int = np.min(mean_int_list)
            #min_int = 0.5*max_int
            #int_TH = 0.5*(min_int + max_int)
            int_TH = Crescent_ratio*(max_int)
            width = np.sum(mean_int_list > int_TH)/nbins
            return width 
           
        features = pd.DataFrame()
        intensityImage = imageItem.image
        THImage = (intensityImage > threshold).astype(int) # relative threshold
        labelImage = skimage.measure.label(THImage)
        regions = skimage.measure.regionprops(label_image=labelImage, intensity_image=intensityImage) # http://scikit-image.org/docs/dev/api/skimage.measure.html
        min_dist_boundray = 15  # in pxl
        dim = len(intensityImage) # assuming an NxN image
        j = 0
        for region in regions:
            if j >= MaxFeatures: # do not add feature
                break
            # area filter and then look for JP close pair indications
            pairTrigger = False
            if region.area < MinArea or region.area > MaxArea or region.eccentricity > MaxElipticity:   # do not add this feature exept check it for pairs
                if SeparateClosePairs and region.area > MinAreaPair and region.area < MaxAreaPair and region.eccentricity > MinElipticityPair:
                    pairTrigger = True
                else:
                    continue # ignor feature if none of this applied
            minYi, minXi, maxYi, maxXi = region.bbox
            if minYi < min_dist_boundray and maxYi > dim-min_dist_boundray and minXi < min_dist_boundray and maxXi > dim-min_dist_boundray: 
                continue
            
            if not pairTrigger:
                x, y, phi = Track_single_JP(intensityImage[minYi:maxYi,minXi:maxXi])
                crescent_width = Crescent_width(intensityImage[minYi:maxYi,minXi:maxXi], x, y, Crescent_ratio)
                
                features = features.append([{'x': x + minYi, # go bak to full image cords
                                   'y': y + minXi,
                                   #'COM_x': orient_x + minYi, 
                                   #'COM_y': orient_y + minXi,
                                   'phi': phi,
                                   'minor_axis_length': region.minor_axis_length,
                                   'major_axis_length': region.major_axis_length,
                                   'area': region.area,
                                   'bbox': region.bbox,
                                   'eccentricity': region.eccentricity,
                                   'hu_moments' : list(region.weighted_moments_hu),
                                   'max_intensity': region.max_intensity,
                                   'summed_intensity': region.area * region.mean_intensity,
                                   'crescent_width' : crescent_width,
                                   'frame': frame,
                                   'ClosePairStatus': pairTrigger,
                                   }])
                j += 1 # feature added
            elif pairTrigger:
                y_com,x_com = region.centroid
                orientation_pair = region.orientation
                masked_images = Make_separated_JP_images(x = x_com-minXi, y = y_com-minYi, phi = orientation_pair, image = intensityImage[minYi:maxYi,minXi:maxXi])
                for masked_image in masked_images:
                    x, y, phi = Track_single_JP(masked_image)
                    features = features.append([{'x': x + minYi, # go bak to full image cords
                                       'y': y + minXi,
                                       'phi': phi,
                                       'minor_axis_length': region.minor_axis_length,
                                       'major_axis_length': region.major_axis_length,
                                       'area': region.area,
                                       'bbox': region.bbox,
                                       'eccentricity': region.eccentricity,
                                       'hu_moments' : region.moments_hu,
                                       'max_intensity': np.max(masked_image),
                                       'summed_intensity': np.sum(masked_image),
                                       'crescent_width' : crescent_width,
                                       'frame': frame,
                                       'ClosePairStatus': pairTrigger,
                                       }])
                    j += 1 # feature added
            ##Overlay (old)
            #if features.size > 0:
            #    
            #    axesX_b = []
            #    axesY_b = []
            #    clist_b = []
            #    axesX_r = []
            #    axesY_r = []
            #    clist_r = []
            #    for index, s in features.iterrows():
            #        # JP Orientation vector
            #        line_length = (s.bbox[2] -  s.bbox[0])/2
            #        axesX_r.extend([s.x, s.x + line_length*np.sin(s.phi)])
            #        axesY_r.extend([s.y, s.y + line_length*np.cos(s.phi)])
            #        clist_r.extend([1,0])
            #        
            #        box_h = s.bbox[2] - s.bbox[0]
            #        box_w = s.bbox[3] - s.bbox[1]
            #        axesX_b.extend([s.x - box_w/2, s.x + box_w/2])
            #        axesY_b.extend([s.y + box_h/2 , s.y + box_h/2])
            #        clist_b.extend([1,0])
            #        axesX_r.extend([s.x - box_w/2, s.x - box_w/2 + s.crescent_width*box_w])
            #        axesY_r.extend([s.y + box_h/2 + 1, s.y + box_h/2 + 1])
            #        clist_r.extend([1,0])
            #        
            #    lp2.setData(x=axesX_r, y=axesY_r, connect=np.array(clist_r))
            #    lp1.setData(x=axesX_b, y=axesY_b, connect=np.array(clist_b))
        
        if self.showThresholdCheckBox.checkState():
            imageItem.setImage(THImage)
        
        # Overlay
        for item in self.items:
            self.p.removeItem(item)
        self.items = []
        if self.showOverlayCheckBox.checkState():
            for i, f in features.iterrows():
                x0 = f.y + 0.5
                y0 = f.x + 0.5
                self.items.append(pgutils.EllipseItem([x0, y0], f.minor_axis_length, f.major_axis_length, -np.degrees(f.phi), color='r', width=2))
                self.p.addItem(self.items[-1])
                #self.items.append(pgutils.LineItem([x0, y0], [x0 + 0.5*f.minor_axis_length*np.cos(f.phi), y0 - 0.5*f.minor_axis_length*np.sin(f.phi)], color='r', width=2))
                #self.p.addItem(self.items[-1])
                self.items.append(pgutils.LineItem([x0, y0], [x0 + 0.5*f.major_axis_length*np.sin(f.phi), y0 + 0.5*f.major_axis_length*np.cos(f.phi)], color='r', width=2))
                self.p.addItem(self.items[-1])
                # JP crescent width bar
                box_h = f.bbox[2] - f.bbox[0]
                box_w = f.bbox[3] - f.bbox[1]
                self.items.append(pgutils.LineItem([x0 - box_w/2, y0 - box_h/4*3], [x0 - box_w/2 + f.crescent_width*box_w, y0 - box_h/4*3], color='r', width=4))
                self.p.addItem(self.items[-1])
                
        
        if features.size > 0:
            self.numberOfFeatures.setText(str(features.shape[0]))
        else:
            self.numberOfFeatures.setText('0')
        
        features.reset_index(drop=True, inplace = True)
        return features#, THImage
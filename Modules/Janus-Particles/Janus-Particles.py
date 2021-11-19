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
        self.MinSphericitySpinBox.valueChanged.connect(self.updated.emit)
        self.SeparateClosePairsCheckBox.stateChanged.connect(self.updated.emit)
        self.MinAreaPairSpinBox.valueChanged.connect(self.updated.emit)
        self.MaxAreaPairSpinBox.valueChanged.connect(self.updated.emit)
        self.MaxSphericityPairSpinBox.valueChanged.connect(self.updated.emit)
        #self.Crescent_ratioSpinBox.valueChanged.connect(self.updated.emit)
        self.UseMinValueCheckBox.stateChanged.connect(self.updated.emit)
        self.RJPSpinBox.valueChanged.connect(self.updated.emit)


    def attach(self, plot):
        self.p = plot
        self.items = []
        restoreSettings(self.settingsFile, self.widget)
        
        
    def detach(self):
        for item in self.items:
            self.p.removeItem(item) 
        saveSettings(self.settingsFile, self.widget)
        

    def findFeatures(self, frame, imageItem):
        from copy import deepcopy
        threshold = self.thresholdSpinBox.value()
        MinArea = self.minAreaSpinBox.value()
        MaxArea = self.maxAreaSpinBox.value()
        MaxFeatures = self.maxFeaturesSpinBox.value()
        #invert = self.invertCheckBox.checkState()
        MinSphericity = self.MinSphericitySpinBox.value()/100
        SeparateClosePairs = self.SeparateClosePairsCheckBox.checkState()
        MinAreaPair = self.MinAreaPairSpinBox.value()
        MaxAreaPair = self.MaxAreaPairSpinBox.value()
        MaxSphericityPair = self.MaxSphericityPairSpinBox.value()/100
        #Crescent_ratio = self.Crescent_ratioSpinBox.value()/100
        UseMinValue = self.UseMinValueCheckBox.checkState()
        RJP = self.RJPSpinBox.value()
        
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
        
        #def Crescent_width(JP_image,x_JP,y_JP,Crescent_ratio):
        #    nbins = 10
        #    phi_edges = np.linspace(-np.pi, np.pi, nbins+1)
        #    #dphi = phi_edges[1] - phi_edges[0]
        #    #phi_mids = phi_edges[:-1] + dphi/2
        #    #i_list = np.arange(nbins)
        #    dimy = np.shape(JP_image)[0]
        #    dimx = np.shape(JP_image)[1]
        #    x_list = np.arange(dimx) - dimx/2
        #    y_list = np.arange(dimy) - dimx/2
        #    x_M, y_M = np.meshgrid(x_list, y_list)
        #    r_M = np.sqrt(x_M**2 + y_M**2)
        #    phi_M = np.arctan2(x_M,y_M)
        #    #phi_hist = np.zeros(nbins)
        #    mean_int_list = np.zeros(nbins)
        #    for i in range(nbins):
        #        #phi_hist[i] = np.sum( (phi_M > phi_edges[i])&(phi_M < phi_edges[i+1]) )
        #        mean_int_list[i] = np.mean( JP_image[(phi_M > phi_edges[i]) & (phi_M < phi_edges[i+1]) & (r_M < np.mean([dimx,dimy])/2)] )
        #    max_int = np.max(mean_int_list)
        #    #min_int = np.min(mean_int_list)
        #    #min_int = 0.5*max_int
        #    #int_TH = 0.5*(min_int + max_int)
        #    int_TH = Crescent_ratio*(max_int)
        #    width = np.sum(mean_int_list > int_TH)/nbins
        #    return width 
           
        features = pd.DataFrame()
        intensityImage = imageItem.image
        THImage = (intensityImage > threshold).astype('int') # relative threshold
        labelImage = skimage.measure.label(THImage)
        regions = skimage.measure.regionprops(label_image=labelImage, intensity_image=intensityImage) # http://scikit-image.org/docs/dev/api/skimage.measure.html
        min_dist_boundray = 15  # in pxl
        dim = len(intensityImage) # assuming an NxN image
        j = 0
        for region in regions:
            if j >= MaxFeatures: # do not add feature
                break
            minYi, minXi, maxYi, maxXi = region.bbox
            # area filter and then look for JP close pair indications
            pairTrigger = False

            if region.area == 1:
                break
            sphericity = region.minor_axis_length/region.major_axis_length

            if region.area < MinArea or region.area > MaxArea or sphericity < MinSphericity:   # do not add this feature but first check it for pairs
                if SeparateClosePairs and region.area > MinAreaPair and region.area < MaxAreaPair and sphericity <= MaxSphericityPair:
                    pairTrigger = True
                else: # its not a JP!
                    y0 = region.centroid[0]
                    x0 = region.centroid[1]
                    features = features.append([{'y': y0, # go bak to full image cords
                                       'x': x0 ,
                                       'bbox': region.bbox,
                                       'frame': frame,
                                       'area': region.area,
                                       'max_intensity': region.max_intensity,
                                       'summed_intensity': region.area * region.mean_intensity,
                                       'is_JP': 0
                                       }])
                    j += 1 # feature added minor_axis_length
                    



                    #IS_JP = 0
                    #sphericity = 0
                    continue # ignor feature if none of this applied
            if minYi < min_dist_boundray and maxYi > dim-min_dist_boundray and minXi < min_dist_boundray and maxXi > dim-min_dist_boundray: 
                continue
            
            if not pairTrigger:
                y, x, phi = Track_single_JP(intensityImage[minYi:maxYi,minXi:maxXi])
                #crescent_width = Crescent_width(intensityImage[minYi:maxYi,minXi:maxXi], x, y, Crescent_ratio)
                
                ## use the intensity minimum to try to correct the position bias from the bright side
                if UseMinValue: 
                    x_bbox_min, y_bbox_min, x_bbox_max, y_bbox_max = np.array([x - RJP, y - RJP, x + RJP, y + RJP]).astype('int') # make image of center of the JP
                    JP_image_smaller = intensityImage[minYi:maxYi,minXi:maxXi][y_bbox_min:y_bbox_max,x_bbox_min:x_bbox_max]
                    
                    TH_center = 1.2*np.min(JP_image_smaller)
                    TH_coords = np.argwhere(JP_image_smaller <= TH_center)
                    x_dark_center = np.mean(TH_coords[:,1]) + x - RJP
                    y_dark_center = np.mean(TH_coords[:,0]) + y - RJP
                    x = (x + x_dark_center)/2
                    y = (y + y_dark_center)/2

                features = features.append([{'y': y + minYi, # go back to full image cords 
                                                'x': x + minXi,
                                                'phi': -(phi - np.pi/2), # also the angle was measured somehow from the wrong axis...
                                                'phi_region': region.orientation,
                                                'minor_axis_length': region.minor_axis_length,
                                                'major_axis_length': region.major_axis_length,
                                                'sphericity': sphericity,
                                                'area': region.area,
                                                'bbox': region.bbox,
                                                'max_intensity': region.max_intensity,
                                                'summed_intensity': region.area * region.mean_intensity,
                                                #'crescent_width' : crescent_width,
                                                'frame': frame,
                                                'ClosePairStatus': pairTrigger,
                                                'is_JP': 1,
                                   }])
                j += 1 # feature added
            elif pairTrigger:
                y_com,x_com = region.centroid
                orientation_pair = region.orientation +np.pi/2
                masked_images = Make_separated_JP_images(x = x_com-minXi, y = y_com-minYi, phi = orientation_pair, image = intensityImage[minYi:maxYi,minXi:maxXi]*region.image)
                for masked_image in masked_images:
                    intensityImage_JP = masked_image
                    THImage_JP = (intensityImage_JP > threshold).astype('int') # relative threshold
                    labelImage_JP = skimage.measure.label(THImage_JP)
                    region_JP = skimage.measure.regionprops(label_image=labelImage_JP, intensity_image=intensityImage_JP)[0]
                    #try:
                    sphericity_JP = region.minor_axis_length/region.major_axis_length
                    #except:
                    #    sphericity_JP = 0
                    #    print('region_JP.bbox',region_JP.bbox)
                    #    print('np.sum(masked_image)',np.sum(masked_image))
                    y, x, phi = Track_single_JP(masked_image)

                    ## use the intensity minimum to try to correct the position bias from the bright side
                    if UseMinValue: 
                        
                        
                        x_bbox_min, y_bbox_min, x_bbox_max, y_bbox_max = np.array([x - RJP, y - RJP, x + RJP, y + RJP]).astype('int') # make image of center of the JP
                        JP_image_smaller = deepcopy(intensityImage[minYi:maxYi,minXi:maxXi][y_bbox_min:y_bbox_max,x_bbox_min:x_bbox_max])
                        JP_image_smaller[JP_image_smaller==0] = np.max(JP_image_smaller) # make all of the zeros very large so that the threshold in the following works fine
                        TH_center = 1.2*np.min(JP_image_smaller)
                        TH_coords = np.argwhere(JP_image_smaller <= TH_center)
                        x_dark_center = np.mean(TH_coords[:,1]) + x - RJP
                        y_dark_center = np.mean(TH_coords[:,0]) + y - RJP
                        
                        x = (x + x_dark_center)/2
                        y = (y + y_dark_center)/2

                    features = features.append([{'y': y + minYi, # go bak to full image cords
                                       'x': x + minXi,
                                       'phi': -(phi - np.pi/2),
                                       'phi_region': region_JP.orientation,
                                       'minor_axis_length': region_JP.minor_axis_length,
                                       'major_axis_length': region_JP.major_axis_length,
                                       'sphericity': sphericity_JP,
                                       'area': region_JP.area,
                                       'bbox': region_JP.bbox,
                                       'max_intensity': np.max(masked_image),
                                       'summed_intensity': np.sum(masked_image),
                                       #'crescent_width' : crescent_width,
                                       'frame': frame,
                                       'ClosePairStatus': pairTrigger,
                                       'is_JP': 1
                                       }])
                    j += 1 # feature added

        if self.showThresholdCheckBox.checkState():
            imageItem.setImage(THImage)
        
        # Overlay
        for item in self.items:
            self.p.removeItem(item)
        self.items = []
        if self.showOverlayCheckBox.checkState():
            for i, f in features.iterrows():                
                if f.is_JP == 1:
                    x0 = f.x + 0.5
                    y0 = f.y + 0.5
                    self.items.append(pgutils.EllipseItem([x0, y0], f.minor_axis_length, f.major_axis_length, -np.degrees(f.phi_region), color='b', width=2))
                    self.p.addItem(self.items[-1])
                    #self.items.append(pgutils.LineItem([x0, y0], [x0 + 0.5*f.minor_axis_length*np.cos(f.phi), y0 - 0.5*f.minor_axis_length*np.sin(f.phi)], color='r', width=2))
                    #self.p.addItem(self.items[-1])
                    self.items.append(pgutils.LineItem([x0, y0], [x0 + 0.5*f.major_axis_length*np.cos(f.phi), y0 + 0.5*f.major_axis_length*np.sin(f.phi)], color='b', width=2))
                    self.p.addItem(self.items[-1])


                else:
                    x0 = f.x + 0.5
                    y0 = f.y + 0.5
                    y_min, x_min, y_max, x_max = f.bbox
                    self.items.append(pgutils.LineItem([x_min, y_min], [x_max, y_max], color='r', width=6))
                    self.p.addItem(self.items[-1])
                    self.items.append(pgutils.LineItem([x_max, y_min], [x_min, y_max], color='r', width=6))
                    self.p.addItem(self.items[-1])



                ## JP crescent width bar
                #box_h = f.bbox[2] - f.bbox[0]
                #box_w = f.bbox[3] - f.bbox[1]
                #self.items.append(pgutils.LineItem([x0 - box_w/2, y0 - box_h/4*3], [x0 - box_w/2 + f.crescent_width*box_w, y0 - box_h/4*3], color='r', width=4))
                #self.p.addItem(self.items[-1])

        if features.size > 0:
            self.numberOfFeatures.setText(str(features.shape[0]))
        else:
            self.numberOfFeatures.setText('0')
        
        features.reset_index(drop=True, inplace = True)
        return features#, THImage
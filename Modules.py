# -*- coding: utf-8 -*-
"""
Discription:
Author: Martin Fränzl
Data: 21/06/18
"""

import numpy as np
import pandas as pd
import skimage
from skimage.feature import blob_log, blob_dog


def ConnectedComponent(i, image, lp1, lp2, **args):
    
    threshold = args['tab1ThresholdSpinBox']
    min_area = args['tab1MinAreaSpinBox']
    max_area = args['tab1MaxAreaSpinBox']
    invert = args['tab1InvertCheckBox']
    max_features = args['tab1MaxFeaturesSpinBox']
    
    features = pd.DataFrame()
    intensityImage = image
    image = (image > threshold).astype(int) # threshold image
    if invert:
        image = 1 - image
    labelImage = skimage.measure.label(image)
    regions = skimage.measure.regionprops(label_image = labelImage, intensity_image = intensityImage) # http://scikit-image.org/docs/dev/api/skimage.measure.html
    j = 0
    for region in regions:
        # area filter first 
        if region.area < min_area or region.area > max_area:  # do not add feature
            continue
        if j >= max_features: # do not add feature
            continue 
        features = features.append([{'y': region.centroid[0], 
									 'x': region.centroid[1],
									 'orientation': region.orientation,
									 'minor_axis_length': region.minor_axis_length,
									 'major_axis_length': region.major_axis_length,
									 'area': region.area,
									 'max_intensity': region.max_intensity,
									 'frame': i,}])
        j += 1 # feature added 		
     
    if features.size > 0:            
        axesX = []
        axesY = []
        axesConnect = []
        ellipsesX = []
        ellipsesY = []
        ellipsesConnect = []
        phi = np.linspace(0, 2*np.pi, 25)
        for index, f in features.iterrows():
            # Ellipse
            x = 0.5*f.minor_axis_length*np.cos(phi)
            y = 0.5*f.major_axis_length*np.sin(phi)
            ellipsesX.extend(f.x +  x*np.sin(f.orientation) - y*np.cos(f.orientation))
            ellipsesY.extend(f.y +  x*np.cos(f.orientation) + y*np.sin(f.orientation))
            connect = np.ones(phi.size)
            connect[-1] = 0 # replace last element with 0
            ellipsesConnect.extend(connect)
            # Axes
            x1 = np.cos(f.orientation)*0.5*f.major_axis_length
            y1 = np.sin(f.orientation)*0.5*f.major_axis_length
            x2 = -np.sin(f.orientation)*0.5*f.minor_axis_length
            y2 = np.cos(f.orientation)*0.5*f.minor_axis_length
            axesX.extend([f.x, f.x + x1, f.x + x2, f.x])
            axesY.extend([f.y, f.y - y1, f.y - y2, f.y])
            axesConnect.extend([1, 0, 1, 0])
            
        lp1.setData(x=axesX, y=axesY, connect=np.array(axesConnect)) 
        lp2.setData(x=ellipsesX, y=ellipsesY, connect=np.array(ellipsesConnect))

        
    return features, image
 
    



def DifferenceOfGaussians(i, image, lp1, lp2, **args):
    
    threshold = args['tab2ThresholdSpinBox']
    max_sigma = args['tab2MaxSigmaSpinBox']
    
    mlist = blob_dog(image/image.max(), max_sigma=max_sigma, threshold=threshold/100)
    
    features = pd.DataFrame()
    if mlist.size > 0:
        radii = mlist[:, 2]*np.sqrt(2)
        mlist[:, 2] = np.pi*(radii)**2 # area
        features = pd.DataFrame(np.transpose([mlist[:,1], mlist[:,0], mlist[:,2], i*np.ones(mlist.shape[0])]), columns=['x', 'y', 'area', 'frame'])
    
    if features.size > 0:            
        circlesX = []
        circlesY = []
        circlesConnect = []
        phi = np.linspace(0, 2*np.pi, 25)
        for index, f in features.iterrows():
            # Circle
            x = radii[index]*np.cos(phi)
            y = radii[index]*np.sin(phi)
            circlesX.extend(f.x +  x)
            circlesY.extend(f.y +  y)
            connect = np.ones(phi.size)
            connect[-1] = 0 # replace last element with 0
            circlesConnect.extend(connect)

        lp2.setData(x=circlesX, y=circlesY, connect=np.array(circlesConnect))
        
        
    return features, image
    
    
    
# -*- coding: utf-8 -*-
"""
Discription: Tracking Module of the Molecular Nanophotonics TrackLab.
Author(s): M. Fränzl, N. Söker
Data: 08/11/18
"""

import numpy as np
import pandas as pd
import skimage
from skimage.feature import blob_log, blob_dog


###############################################################################
# Method:       Connected-Component Labeling
# Discription:  Simple feature detection algorithm similar to the one
#               used in LabVIEW
# 
###############################################################################
def ConnectedComponent(i, image, lp1, lp2, **args):
    
    threshold = args['tab1ThresholdSpinBox']
    min_area = args['tab1MinAreaSpinBox']
    max_area = args['tab1MaxAreaSpinBox']
    invert = args['tab1InvertCheckBox']
    max_features = args['tab1MaxFeaturesSpinBox']
    
    # Detect features
    features = pd.DataFrame()
    intensityImage = image
    image = (image > threshold).astype(int) # Threshold image
    if invert:
        image = 1 - image
    labelImage = skimage.measure.label(image)
    regions = skimage.measure.regionprops(label_image = labelImage, intensity_image = intensityImage) # http://scikit-image.org/docs/dev/api/skimage.measure.html
    j = 0
    for region in regions:
        # Area filter first 
        if region.area < min_area or region.area > max_area:  # Do not add feature
            continue
        if j >= max_features: # Do not add feature
            continue 
        features = features.append([{'y': region.centroid[0], 
        						     'x': region.centroid[1],
                                     'y_weighted': region.weighted_centroid[0],
                                     'x_weighted': region.weighted_centroid[1],
    								 'orientation': region.orientation,
    								 'minor_axis_length': region.minor_axis_length,
    								 'major_axis_length': region.major_axis_length,
    								 'area': region.area,
                                     'equivalent_diameter': region.equivalent_diameter,
                                     'filled_area': region.filled_area,
    								 'max_intensity': region.max_intensity,
                                     'mean_intensity': region.mean_intensity,
                                     #'bbox': region.bbox,
                                     'eccentricity': region.eccentricity,
                                     #'weighted_moments_central': region.weighted_moments_central,
                                     #'inertia_tensor': region.inertia_tensor,
    								 'frame': i,}])
        j += 1 # feature added
    features.reset_index(drop=True, inplace = True)
    
    # Draw the overlay: Ellipses with minor and major axis. There is no build-in function for ellipses in PyQtGraph, so we draw them using the plotCurveItems lp2.
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
            connect[-1] = 0 # Replace last element with 0
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
 
    

###############################################################################
# Method: Difference of Gaussians
# Discription:
# 
###############################################################################
def DifferenceOfGaussians(i, image, lp1, lp2, **args):
    
    threshold = args['tab2ThresholdSpinBox']
    max_sigma = args['tab2MaxSigmaSpinBox']
    
    mlist = blob_dog(image/image.max(), max_sigma=max_sigma, threshold=threshold/100)
    radii = mlist[:, 2]*np.sqrt(2)
    
    features = pd.DataFrame()
    X,Y = np.meshgrid(np.arange(0, image.shape[0], 1), np.arange(0, image.shape[1], 1))
    if mlist.size > 0:
        for j in range(mlist.shape[0]):
            mask = (((X - mlist[j, 1])**2 + (Y - mlist[j, 0])**2) < (mlist[j, 2]*np.sqrt(2))**2).astype(int)
            features = features.append([{'y': mlist[j, 0], 
    								     'x': mlist[j, 1],
                                         'max_intensity': image[mask==1].max(),
									     'area': 2*np.pi*mlist[j, 2]**2,
									     'frame': i,}])    

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
    
    
#### JP TRACKER
# - multiple JPs in darkfield illumination
# - can recognize 2 close JPs by ellipticity and size and Track both seperatly
def JPTracker(i, image, lp1, lp2, **kwargs):
    # get all the params set in the JP Tracker tab
    threshold = kwargs['tab3ThresholdSpinBox']
    MinArea = kwargs['tab3MinAreaSpinBox']
    MaxArea = kwargs['tab3MaxAreaSpinBox']
    MaxElipticity = kwargs['tab3MaxElipticitySpinBox'] * 0.1
    SeparateClosePairs = kwargs['SeparateClosePairsCheckBox'] #.checkState() ?
    MinAreaPair = kwargs['tab3MinAreaPairSpinBox']
    MaxAreaPair = kwargs['tab3MaxAreaPairSpinBox']
    MinElipticityPair = kwargs['tab3MinElipticityPairSpinBox'] * 0.1
    MaxFeatures = kwargs['tab3MaxFeaturesSpinBox']
    
    
    def Threshold(frame,TH,new_value,**kwargs):
        """eats a xy grayscale image and applys threshold TH with new value. 
        ad 'both' or 'inverse' as kwargs, you can also set a new upper value"""
        kwargs.setdefault('mode', 'normal')#set default values for kwargs
        if kwargs.get('mode') == 'inverse':
            indices = frame > TH #make an index list of values forfilling the condition
            frame[indices] = new_value
        elif kwargs.get('mode')=='both':
            indices = frame < TH
            frame[indices]=0
            indices = frame >= TH
            frame[indices] = 1
        elif kwargs.get('mode')=='normal':
            indices = frame < TH
            frame[indices]=new_value
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
    
    def Crescent_width(JP_image,x_JP,y_JP):
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
        #r_M = np.sqrt(x_Mx**2 + y_M**2)
        phi_M = np.arctan2(x_M,y_M)
        #phi_hist = np.zeros(nbins)
        mean_int_list = np.zeros(nbins)
        for i in range(nbins):
            #phi_hist[i] = np.sum( (phi_M > phi_edges[i])&(phi_M < phi_edges[i+1]) )
            mean_int_list[i] = np.mean( JP_image[(phi_M > phi_edges[i])&(phi_M < phi_edges[i+1])] )
        max_int = np.max(mean_int_list)
        #min_int = np.min(mean_int_list)
        min_int = 0.5*max_int
        int_TH = 0.5*(min_int + max_int)
        width = np.sum(mean_int_list < int_TH)/nbins
        return width 
       
    features = pd.DataFrame()
    intensityImage = image
    THImage = (image > threshold).astype(int) # relative threshold
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
            crescent_width = Crescent_width(intensityImage[minYi:maxYi,minXi:maxXi], x, y)
            
            features = features.append([{'y': x + minYi, # go bak to full image cords
                               'x': y + minXi,
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
                               'frame': i,
                               'ClosePairStatus': pairTrigger,
                               }])
            j += 1 # feature added
        elif pairTrigger:
            y_com,x_com = region.centroid
            orientation_pair = region.orientation
            masked_images = Make_separated_JP_images(x = x_com-minXi, y = y_com-minYi, phi = orientation_pair, image = intensityImage[minYi:maxYi,minXi:maxXi])
            for masked_image in masked_images:
                x, y, phi = Track_single_JP(masked_image)
                features = features.append([{'y': x + minYi, # go bak to full image cords
                                   'x': y + minXi,
                                   'phi': phi,
                                   'minor_axis_length': region.minor_axis_length,
                                   'major_axis_length': region.major_axis_length,
                                   'area': region.area,
                                   'bbox': region.bbox,
                                   'eccentricity': region.eccentricity,
                                   'hu_moments' : region.moments_hu,
                                   'max_intensity': np.max(masked_image),
                                   'summed_intensity': np.sum(masked_image),
                                   'frame': i,
                                   'ClosePairStatus': pairTrigger,
                                   }])
                j += 1 # feature added

        if features.size > 0:
            axesX2 = []
            axesY2 = []
            clist = []
            for index, s in features.iterrows():
                # JP Orientation vector
                line_length = 8
                axesX2.extend([s.x, s.x + line_length*np.sin(s.phi)])
                axesY2.extend([s.y, s.y + line_length*np.cos(s.phi)])
                clist.extend([1,0])
            lp1.setData(x=axesX2, y=axesY2, connect=np.array(clist))
    return features, THImage









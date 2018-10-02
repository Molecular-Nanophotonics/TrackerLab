# TrackerLab

## Contents

- [Discription](#discription)
- [Sample Data](#data-availability)
- [Installation Guide](#installation-guide)
- [Instructions for Use](#instructions-for-use)
- [Notebooks](#Notebooks)


## Discription

This is the repository for the Molecular Nanophotonics TrackerLab. It is a modular GUI writen in Python for the tracking of nano-objects based on PyQt and PyQtGraph.

## Sample Data

A sample dataset for testing is available at: ...

## Installation Guide

The TrackerLab supports Windows, Mac OS and Linux and requires the [Anaconda](https://www.anaconda.com/download/) framework with Python 3 to be installed. 

### Required Packages:

In addition the following Python packages are required:

1. nptdms
2. pyqtgraph

To use the Video Export functionality FFmpeg needs to be installed.

## Instructions for Use

To start the TrackerLab run `TrackerLab.py`

If all required packages are installed properly you should see something similar to:
![Screenshot](https://github.com/Molecular-Nanophotonics/TrackerLab/blob/master/Resources/Screenshot.PNG)

To get started click `Select...` and select a set of `*_movie.tdms` files for investigation. Currently, the software supports our custom TDMS files (`*_movie.tdms`) and stacked TIFF files for more general use. `Add...` and `Remove` can be used to add and remove files from the file list. The file dialog as well as the file list supports multiple file selection. Sorting in the file list via drag and drop is currently not supported (Will be added in the future). The displayed file is marked with black dot and can be selected by double-clicking in the file list. The left graph shows the raw image and the right graph the process image and the overlay.

In the pre-processing panel a media filter and a circular mask can be applied to the image.  

In the tracking tab the tracking method and the parameters can be selected. 

To process all files in the file list click `Start`. Depending on the `Settings` the tracking data will be stored as `*_features.h5` HDF5 file or as `*_features.csv` CSV file.

## Jupyter Notebooks

[FeaturesFileReader.ipynb](https://github.com/Molecular-Nanophotonics/TrackerLab/blob/master/Jupyter-Notebooks/FeaturesFileReader.ipynb) demonstates how to read the exported  HDF5 and CSV feature files.

## Adding New Feature Detection Tabs

The software is designed modular making it easy to add custom feature detection tabs. To add a new tab open the `TrackerLab.ui` file with the *Qt Designer* contained in your Anacoda installation. Then, right-click the tab widget, add a new tab and insert the required input widgets and labels. Later, the values of your input widgets will be accessed by their object name. To implement your detection method open the file `Modules.py` and add a new function with the follwing structure:
```
def MyDetection(i, image, lp1, lp2, **args):

    value1 = args['value1SpinBox']
    value2 = args['value2SpinBox']
    ...
    
    # Detect Features
    features = pd.DataFrame() # The first return value has to be a data frame
    ...
    
    # Draw the Overlay
    ...
    
return features, image
```
The name of your function has to match the tab name in `TrackerLab.ui`. The default arguments of the function are the frame number `i`, a 2D array `image` containing the image and two line plot items `lp1` and `lp2` for the overlay. The argument `args` contains the values of your input widgets defined by their object name.




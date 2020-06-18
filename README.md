# TrackerLab v2.2

*Martin Fränzl*, Molecular Nanophotonics Group, Universität Leipzig

## Contents

- [Discription](#discription)
- [Sample Data](#sample-data)
- [Installation Guide](#installation-guide)
- [Instructions for Use](#instructions-for-use)
- [Jupyter-Notebooks](#jupyter-notebooks)
- [Adding New Feature Detection Tabs](#adding-new-feature-detection-tabs)


## Discription

This is the repository for the Molecular Nanophotonics TrackerLab. It is a modular GUI writen in Python for detecting features in digital microscopy images based on PyQt and PyQtGraph.

## Installation Guide

The TrackerLab supports Windows, Mac OS and Linux and requires the [Anaconda](https://www.anaconda.com/download/) framework with Python 3 to be installed. 

### Required Packages:

The following extra packages are required:

1. nptdms
2. pyqtgraph

The FFmpeg binaries required for the Video Export function are included in this repository. If you have FFmpeg already installed, TrackerLab will use your installation instead.

## Instructions for Use

Start the TrackerLab with: `python TrackerLab.py`

If all required packages are installed properly you should see something similar to: <br>

![Screenshot](https://github.com/Molecular-Nanophotonics/TrackerLab/blob/master/Resources/Screencapture.gif)

To get started click `Select...` and select a set of `*_video.tdms` files for investigation. Currently, the software supports our custom TDMS files (`*_video.tdms`), stacked TIFF files as well as MP4 files. `Add...` and `Remove` can be used to add and remove files from the file list. The file dialog as well as the file list supports multiple file selection. The displayed file is marked with black dot and can be changed by double-clicking. The left image view shows the raw image and the right image view the processed image with the feature detection overlay.

In the pre-processing panel several filter and a circular mask can be applied to the image.  

In the feature detection tab the detection method and the parameters can be selected. 

Click `Batch` to process all files in the file list. Depending on the settings (`Edit > Settings`) the feature detection data will be stored as `*_features.csv` CSV file or as `*_features.h5` HDF5 file. See the [Jupyter-Notebooks](#jupyter-notebooks) section for more information on how to read the files in Jupyter-Notebooks. 

## Sample Data

A sample dataset for testing is available at: .`73/Sample Data`

## Jupyter Notebooks

[Read_Features_Files.ipynb](https://github.com/Molecular-Nanophotonics/TrackerLab/blob/master/Jupyter-Notebooks/Read_Features_Files.ipynb) demonstates how to read the exported CSV and HDF5 feature files.

For more information on how to work with `*_feature` files and DataFrames in general see: [Getting Started with Python in the Molecular Nanophotonics Group](https://github.com/Molecular-Nanophotonics/Jupyter-Notebooks/blob/master/GETTING_STARTED.ipynb)

## Adding New Feature Detection Tabs

The software has a modular design making it easy to add new feature detection tabs. To add a new module tab, enter `MODULES` and copy the `Template` directory. Then, rename the directory as well as the file within the directory according to your module name, e.g., `Module`:
```
--MODULES
  |--Template
  |  |--Template.py
  |  |--Template.ui
  |--Module
  |  |--Module.py
  |  |--Module.ui
```
Then, enter the `MyModule` folder and rename the `Template.py` and `Template.ui` files accordingly, i.e., `MyModule.py` and `MyModule.ui`. The new module will be automatically loaded when restarting the application. To learn how a module works, open the `MyModule.py` and read the comments. The `MyModule.ui` can be edited with the *Qt Designer* contained in your Anacoda installation.



# Tracking and Data Analysis of Single Amyloid Fibrils in a Thermophoretic Trap

## Contents

- [Discription](#discription)
- [Sample Data](#data-availability)
- [Installation Guide](#installation-guide)
- [Instructions for Use](#instructions-for-use)
- [Notebooks](#Notebooks)


## Discription

This is the repository for the *"TrackerLab"* of the Molecular Nanophotonics Group. It is a GUI for image processing, tracking and video conversion based on PyQt, PyQtGraph packages and FFmpeg.

## Sample Data

A sample dataset for testing is available at: ...

## System Requirements

The TrackerLab is supported for Windows, Mac OS and Linux. The software has been tested on the following systems:

Windows: 10  
Mac OS: 10.12  
Linux:   

## Installation Guide

The software requires the [Anaconda](https://www.anaconda.com/download/) framework with Python 3 to be installed. 

### Required Packages:

The following packages are required:

1. nptdms
2. pyqtgraph
3. ffmpeg (optional)

## Instructions for Use

Then, run the TrackerLab.py script. With all packages installed properly you should see a GUI similar to the screenshot below. 
To open a video file click `Open...` and select all `*_video.tdms` in the sample dataset.

![Screenshot](https://github.com/Molecular-Nanophotonics/Thermophoretic-Trap-for-Protein-Aggregation-Studies/blob/master/Resources/Screenshot.PNG)

The `*video.tdms` files are TDMS files recored with LabVIEW containing the image series and metadata such as the binning and the exposure time. For more information about the TDMS file format see [The NI TDM File Format](http://www.ni.com/white-paper/3727/en/).  
Beside these TDMS files the software also supports stacked TIFF files for general use.  
  
In the pre-processing panel a media filter and a circular mask can be applied to the image.
In the tracking tab the tracking method and parameters can be adjusted.

To run the tracking algorithm for all selected files click `Start`. The tracking data will be stored as a DataFrame `features` in a HDF5 file along with the metadata. 

## Jupyter Notebooks

[Step_Size_Analysis.ipynb](https://github.com/Molecular-Nanophotonics/TrackerLab/blob/master/Jupyter-Notebooks/HDF5FileLoader.ipynb) demonstate how to load the HDF5 features files. 


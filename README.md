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

## System Requirements

The TrackerLab supports Windows, Mac OS and Linux. It has been tested on the following systems:

Windows: 10  
Mac OS: 10.12  
Linux: -  

## Installation Guide

The TrackerLab supports Windows, Mac OS and Linux and requires the [Anaconda](https://www.anaconda.com/download/) framework with Python 3 to be installed. 

### Required Packages:

In addition, the following Python packages are required:

1. nptdms
2. pyqtgraph

To use the Video Export functionality FFmpeg needs to be installed.


## Instructions for Use

To start the TrackerLab run script TrackerLab.py with: `python TrackerLab.py`

If all required packages are installed properly you should see something similar to:
![Screenshot](https://github.com/Molecular-Nanophotonics/TrackerLab/blob/master/Resources/Screenshot.PNG)

To get started, click `Select...` and select a set of `*_movie.tdms` files. The TrackerLab support TDMS files and stacked TIFF files.  

  
In the pre-processing panel a media filter and a circular mask can be applied to the image.
In the tracking tab the tracking method and parameters can be adjusted.

To run the tracking algorithm for all selected files click `Start`. The tracking data will be stored as a DataFrame `features` in a HDF5 file along with the metadata. 

## Jupyter Notebooks

[HDF5FileLoader.ipynb](https://github.com/Molecular-Nanophotonics/TrackerLab/blob/master/Jupyter-Notebooks/HDF5FileLoader.ipynb) demonstate how to load the HDF5 features files. 

## Writing your Own Module



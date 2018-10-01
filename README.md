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

To start the TrackerLab run script TrackerLab.py with: `python TrackerLab.py`

If all required packages are installed properly you should see something similar to:
![Screenshot](https://github.com/Molecular-Nanophotonics/TrackerLab/blob/master/Resources/Screenshot.PNG)

To get started, click `Select...` to select a set of `*_movie.tdms` files. At present, the software supports our custom TDMS files (`*_movie.tdms`) and stacked TIFF files for general use. Use `Add...` and `Remove` to add and remove files from the file list. The file dialog as well as the file list supports multiple file selection. The displayed file is marked with black dot and can be selected by double-clicking. The left graph shows the raw image and the right graph the process image with the overlay.

In the pre-processing panel a media filter and a circular mask can be applied to the image.  

In the tracking tab the tracking method and the parameters can be selected. 

To process all files in the file list click `Start`. Depending on the `Settings` the tracking data will be stored as `*_features.h5` HDF5 file or as `*_features.csv` CSV file.

## Jupyter Notebooks

[HDF5FileLoader.ipynb](https://github.com/Molecular-Nanophotonics/TrackerLab/blob/master/Jupyter-Notebooks/HDF5FileLoader.ipynb) demonstate how to load and handle the HDF5 features files. 

## Adding New Modules



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

To get started, click `Select...` and select a set of `*_movie.tdms` files. The software suports a specific TDMS files and stacked TIFF files for general use. In the pre-processing panel a media filter and a circular mask can be applied to the images. In the tracking tab the tracking method and parameters can be selected. 
Click `Start` tp process . 
Depending on the selected Setting the tracking data will be stored as DataFrame in a `*_features.h5` HDF5 file along with some metadata. 

## Jupyter Notebooks

[HDF5FileLoader.ipynb](https://github.com/Molecular-Nanophotonics/TrackerLab/blob/master/Jupyter-Notebooks/HDF5FileLoader.ipynb) demonstate how to load and handle the HDF5 features files. 

## Adding New Modules



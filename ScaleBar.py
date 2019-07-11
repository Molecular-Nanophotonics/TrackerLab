# -*- coding: utf-8 -*-
"""
Discription: Scale Bar Class for TrackerLab
Author(s): M. Fränzl
Data: 19/06/11
"""

import numpy as np

from PyQt5.QtWidgets import QDialog
from PyQt5.uic import loadUi

import pyqtgraph as pg
from pyqtgraph import QtCore, QtGui


class ScaleBarDialog(QDialog):
    def __init__(self):
        super().__init__(None,  QtCore.Qt.WindowCloseButtonHint)
        
        loadUi('ScaleBarDialog.ui', self)
        
        
# Class for Scale Bar 
class ScaleBar:
    
    def __init__(self):

        self.settingsDialog = ScaleBarDialog()
        self.bar = QtGui.QGraphicsRectItem()
        self.label = QtGui.QGraphicsSimpleTextItem()
        
        self.dimx = 100
        self.dimy = 100
        
        self.sbColor = QtGui.QColor('#ffffff')
        self.settingsDialog.sbColorPreview.setStyleSheet('background-color: #ffffff')
        
        self.settingsDialog.scaleSpinBox.valueChanged.connect(self.render)
        self.settingsDialog.sbAutoButton.clicked.connect(self.setAuto)
        self.settingsDialog.sbLengthSpinBox.valueChanged.connect(self.render)
        self.settingsDialog.sbXSpinBox.valueChanged.connect(self.render)
        self.settingsDialog.sbYSpinBox.valueChanged.connect(self.render)
        self.settingsDialog.sbLabelYOffsetSpinBox.valueChanged.connect(self.render)
        self.settingsDialog.sbColorButton.clicked.connect(self.openColorDialog)
        self.settingsDialog.sbHeightSpinBox.valueChanged.connect(self.render)
        self.settingsDialog.okButton.clicked.connect(self.settingsDialog.close)


    def add(self, p):
        p.addItem(self.bar)
        p.addItem(self.label)
      
        
    def sizeChanged(self, dimx, dimy):
        self.dimx = dimx
        self.dimy = dimy
        self.render()

        
    def render(self):
        scale = self.settingsDialog.scaleSpinBox.value()
        sbX = self.settingsDialog.sbXSpinBox.value()*self.dimx
        sbY = self.settingsDialog.sbYSpinBox.value()*self.dimy
        sbLabelYOffset = self.settingsDialog.sbLabelYOffsetSpinBox.value()*self.dimy
        sbWidth = int(np.round(self.settingsDialog.sbLengthSpinBox.value()/scale))
        sbHeight = self.settingsDialog.sbHeightSpinBox.value()*self.dimy
        
        # Bar 
        self.bar.setRect(sbX - sbWidth/2, sbY - sbHeight/2, sbWidth, sbHeight)
        self.bar.setPen(pg.mkPen(None))
        self.bar.setBrush(self.sbColor)
           
        # Label
        self.label.setText(str(self.settingsDialog.sbLengthSpinBox.value()) + " \u03bcm")
        self.label.setFont(QtGui.QFont("Helvetica", 0.04*self.dimy)) # (self.dimx + self.dimy)/2
        self.label.setBrush(self.sbColor)
        bRect = self.label.boundingRect()
        self.label.setPos(sbX - bRect.width()/2, sbY - bRect.height()/2 - sbLabelYOffset)
        
        
    def showSettingsDialog(self):
        self.settingsDialog.show()
        
        
    def setVisible(self, state): 
        self.bar.setVisible(state)
        self.label.setVisible(state)
        
        
    def openColorDialog(self):
        self.sbColor = QtGui.QColorDialog.getColor()
        self.settingsDialog.sbColorPreview.setStyleSheet("background-color: %s" % self.sbColor.name())
        self.render()


    def restoreSettings(self, group, settings):
        self.settingsDialog.scaleSpinBox.setValue(float(settings.value(group + '/' + 'Scale', '0.1')))
        self.settingsDialog.sbLengthSpinBox.setValue(int(settings.value(group + '/' + 'Length', '5')))
        self.settingsDialog.sbXSpinBox.setValue(float(settings.value(group + '/' + 'X', '0.80')))
        self.settingsDialog.sbYSpinBox.setValue(float(settings.value(group + '/' + 'Y', '0.90')))
        self.settingsDialog.sbLabelYOffsetSpinBox.setValue(float(settings.value(group + '/' + 'LabelYOffset', '0.05'))) 
        self.sbColor = QtGui.QColor(settings.value(group + '/' + 'Color', '#ffffff'))
        self.settingsDialog.sbColorPreview.setStyleSheet("background-color: %s" % self.sbColor.name())
        
        
    def saveSettings(self, group, settings):
        settings.setValue(group + '/' + 'Scale', self.settingsDialog.scaleSpinBox.value())
        settings.setValue(group + '/' + 'Length', self.settingsDialog.sbLengthSpinBox.value())
        settings.setValue(group + '/' + 'X', self.settingsDialog.sbXSpinBox.value())
        settings.setValue(group + '/' + 'Y', self.settingsDialog.sbYSpinBox.value())
        settings.setValue(group + '/' + 'LabelYOffset', self.settingsDialog.sbLabelYOffsetSpinBox.value())
        settings.setValue(group + '/' + 'Color', self.sbColor.name())
        
        
    def setAuto(self):
        scale = self.settingsDialog.scaleSpinBox.value()   
        suggested_relative_scalebar_width = 0.2
        sb_height_k = 0.02
        sb_right_edge_k = 0.90
        sb_bot_pos_k = 0.92 
        allowed_first_digit = np.array([1, 2, 3, 5, 10]) # the 10 in here is important (the numbersystem hoping point or whaterver its called)
        short_dim_i = np.min([self.dimx,self.dimy]) 
        long_dim_i = np.max([self.dimx,self.dimy])
        max_xy_ratio = 2/3
        if max_xy_ratio * long_dim_i > short_dim_i: # for large aspect ratios take the shorter axis for the auto scale
            W_m = short_dim_i * scale
        else:
            W_m = long_dim_i * scale
        suggested_sblength_m = ( 10**int('{:.0e}'.format(W_m * suggested_relative_scalebar_width)[2:]) 
                                 * allowed_first_digit[np.abs(int('{:.0e}'.format(W_m * suggested_relative_scalebar_width)[0]) - allowed_first_digit).min()
                                 == np.abs(int('{:.0e}'.format(W_m * suggested_relative_scalebar_width)[0])-allowed_first_digit)
                             ][0]
                            )
        
        sblength_i = suggested_sblength_m/scale
        sblength_k = sblength_i/self.dimx
        sb_x_center_i = (sb_right_edge_k - sblength_k/2) * self.dimx
        sb_x_center_k = sb_x_center_i / self.dimx
        sb_y_center_k = sb_bot_pos_k - sb_height_k/2
        sb_height_k/2
        
        self.settingsDialog.sbLengthSpinBox.setValue(suggested_sblength_m)
        self.settingsDialog.sbHeightSpinBox.setValue(sb_height_k)
        self.settingsDialog.sbXSpinBox.setValue(sb_x_center_k)
        self.settingsDialog.sbYSpinBox.setValue(sb_y_center_k)
        self.settingsDialog.sbLabelYOffsetSpinBox.setValue(sb_height_k + 0.04)
        
        self.render()
    

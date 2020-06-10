from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import QWidget


def restoreSettings(fileName, widget):            

    settings = QSettings(fileName, QSettings.IniFormat)
    
    try:    
        for obj in widget.findChildren(QWidget):
            if obj.metaObject().className() == 'QSpinBox':
                obj.setValue(int(settings.value(obj.objectName())))
            if obj.metaObject().className() == 'QDoubleSpinBox':
                obj.setValue(float(settings.value(obj.objectName())))
            if obj.metaObject().className() == 'QCheckBox':
                obj.setCheckState(int(settings.value(obj.objectName())))
            #if obj.metaObject().className() == 'QLineEdit':
            #    obj.setText(str(settings.value(obj.objectName())))
    except:
        print('Error loading ' + settings.fileName()  + '. A new INI file will be created.')
        settings.remove('') # Clear the Settings.ini file  
          
        
def saveSettings(filename, widget):
     
    settings = QSettings(filename, QSettings.IniFormat)  # settings = QSettings(QSettings.IniFormat, QSettings.UserScope, "TrackerLab", "Settings") 

    for obj in widget.findChildren(QWidget):
        if obj.metaObject().className() == 'QSpinBox':
            settings.setValue(obj.objectName(), str(obj.value()))
        if obj.metaObject().className() == 'QDoubleSpinBox':
            settings.setValue(obj.objectName(), str(obj.value()))
        if obj.metaObject().className() == 'QCheckBox':
            settings.setValue(obj.objectName(), str(obj.checkState()))
        #if obj.metaObject().className() == 'QLineEdit':
        #    settings.setValue(obj.objectName(), str(obj.text()))



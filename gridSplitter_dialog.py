# -*- coding: utf-8 -*-
"""
/***************************************************************************
 gridSplitterDialog
                                 A QGIS plugin
 A plugin that cuts a layer into pieces(tiles)
                             -------------------
        begin                : 2015-03-26
        git sha              : $Format:%H$
        copyright            : (C) 2015 by Maximilian Krambach
        email                : maximilian.krambach@gmx.de
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os
from PyQt4 import QtCore, QtGui, uic

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'gridSplitter_dialog_base.ui'))

class gridSplitterDialog(QtGui.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        super(gridSplitterDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.button_box.accepted.connect(self.run)
        self.button_box.rejected.connect(self.close)
        self.cmdBrowseOutput.clicked.connect(self.output_path)
        self.cmdBrowsetmp.clicked.connect(self.tmp_shp_path)
     
    def output_path(self):
       self.dirname = str(QtGui.QFileDialog.getExistingDirectory(self, "Select Directory"))
       self.OuptDir.clear()
       self.OuptDir.setText(self.dirname)
       
    def tmp_shp_path(self):
       self.shapename = str(QtGui.QFileDialog.getSaveFileName(None,"Create Shapefile", '', '*.shp'))
       self.tempFile.clear()
       self.tempFile.setText(self.shapename)
    
    def run(self):
      pass
      return
    
    def close(self):
      pass

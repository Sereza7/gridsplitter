# -*- coding: utf-8 -*-
"""
/***************************************************************************
 gridSplitter
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
from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, QFileInfo
from PyQt4.QtGui import QAction, QIcon, QMessageBox
# Initialize Qt resources from file resources.py
import resources_rc
# Import the code for the dialog
from gridSplitter_dialog import gridSplitterDialog
import os.path
from qgis.core import * 
import processing
import os
import math




class gridSplitter:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'gridSplitter_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Create the dialog (after translation) and keep reference
        self.dlg = gridSplitterDialog()

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&gridSplitter')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'gridSplitter')
        self.toolbar.setObjectName(u'gridSplitter')

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        return QCoreApplication.translate('gridSplitter', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
      
        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/gridSplitter/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Cut layer to pieces'),
            callback=self.run,
            parent=self.iface.mainWindow())


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&gridSplitter'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar


    def run(self):
      """Run method that performs all the real work"""
      # show the dialog
      #loop for the GUI until each required parameter is checked
      chekk="0"
      while chekk != "1": 
	  self.dlg.show()
	  # Run the dialog event loop
	  result = self.dlg.exec_()
	  if result:
	    #get parameters from GUI
	    outputfolder = self.dlg.OuptDir.text()
	    splicesX = int(self.dlg.splicesXSpinBox.text())
	    splicesY = int(self.dlg.splicesYSpinBox.text())
	    rastermap = self.dlg.inputRasterBox.currentLayer()
	    tempfile = self.dlg.tempFile.text()
	    pref = self.dlg.prefixx.text()
	    if rastermap != "":
	     if outputfolder!="":
		#TODO: check if it is a valid path
		  if tempfile !="":
		    if tempfile.upper().endswith(".SHP"):
		      pass
		    else: 
		      tempfile= tempfile + ".shp"
		    if os.path.isfile(tempfile) == True:
		      QMessageBox.information(None,"Shapefile exists!", "Please specify a shapefile that doesn't exist. The shapefile will be overwritten and deleted")
		    else:
		      #now everything is checked, run the code
		      chekk="1" #to end the GUI loop
		      if not os.path.exists(outputfolder):
			os.makedirs(outputfolder)
		      xmax = rastermap.extent().xMaximum()
		      xmin = rastermap.extent().xMinimum()
		      ymax = rastermap.extent().yMaximum()
		      ymin = rastermap.extent().yMinimum()
		      crs= rastermap.crs()
		      
		      if rastermap.type()== QgsMapLayer.RasterLayer:
			  rwidth = rastermap.width()
			  rheight = rastermap.height()
			  xres = (xmax-xmin)/rwidth
			  yres = (ymax-ymin)/rheight
			  #determine slice size, add empty pixels if it doesn't sum up,
			  #making the result stlightly larger. 
			  #make sure that each slice pixel is in the resolution of 
			  #raster, to avoid gaps
			  ixx= float(rwidth)/splicesX
			  iyy= float(rheight)/splicesY
			  xsplice = math.ceil(ixx) * xres
			  ysplice = math.ceil(iyy) * yres
			  #iterate
			  for i in range(splicesX):
			    for j in range(splicesY):
				xsplmin= xmin + i*xsplice
				xsplmax= xmin + (i+1)*xsplice
				ysplmin= ymin + j*ysplice
				ysplmax = ymin + (j+1)*ysplice
				#make a temporary Polygon
				tmpf= "Polygon?crs="+ crs.authid()
				gridtmp = QgsVectorLayer(tmpf, "gridtile", "memory")
				QgsMapLayerRegistry.instance().addMapLayer(gridtmp)
				gridtmp.startEditing()
				pol= "POLYGON (("+str(xsplmin)+" "+str(ysplmin)+", "+str(xsplmax)+" "+str(ysplmin)+", "+str(xsplmax)+" "+str(ysplmax)+", "+str(xsplmin)+" "+str(ysplmax)+", "+str(xsplmin)+" "+str(ysplmin)+ "))"
				fet = QgsFeature()
				pr= gridtmp.dataProvider()
				fet.setGeometry(QgsGeometry.fromWkt(pol))
				pr.addFeatures( [ fet ] )
				gridtmp.commitChanges()
				#write it to tempfile. Needed, because gdalogr doesn't seem to accept memory layer?
				writer = QgsVectorFileWriter.writeAsVectorFormat(gridtmp, tempfile,"utf-8",crs,"ESRI Shapefile")
				folder= outputfolder + os.sep + str(i)+os.sep + str(j)+ os.sep
				if not os.path.exists(folder):
				    os.makedirs(folder)
				
				processing.runalg('gdalogr:cliprasterbymasklayer', rastermap, tempfile , None, False, False, "",folder +pref + str(i)+"_"+str(j)+".tif")
				
				if self.dlg.addTiles.isChecked()== True:
				  #add raster layer to canvas
				  fileInfo = QFileInfo(folder +pref + str(i)+"_"+str(j)+".tif")
				  baseName = fileInfo.baseName()
				  layer = QgsRasterLayer(folder +pref + str(i)+"_"+str(j)+".tif", baseName)
				  QgsMapLayerRegistry.instance().addMapLayer(layer)
 				
				#clean up
				QgsMapLayerRegistry.instance().removeMapLayers( [gridtmp.id()] )
				if os.path.isfile(tempfile):
				    QgsVectorFileWriter.deleteShapeFile(tempfile)           
		      else:
			if rastermap.type()== QgsMapLayer.VectorLayer:
			  xsplice = (ymax - ymin)/splicesX
			  ysplice = (ymax - ymin)/splicesX
			  for i in range(splicesX):
			    for j in range(splicesY):
			      xsplmin= xmin + i*xsplice
			      xsplmax= xmin + (i+1)*xsplice
			      ysplmin= ymin + j*ysplice
			      ysplmax = ymin + (j+1)*ysplice
			      #make a temporary polygon
			      tmpf= "Polygon?crs="+ crs.authid()
			      gridtmp = QgsVectorLayer(tmpf, "gridtile", "memory")
			      QgsMapLayerRegistry.instance().addMapLayer(gridtmp)
			      gridtmp.startEditing()
			      pol= "POLYGON (("+str(xsplmin)+" "+str(ysplmin)+", "+str(xsplmax)+" "+str(ysplmin)+", "+str(xsplmax)+" "+str(ysplmax)+", "+str(xsplmin)+" "+str(ysplmax)+", "+str(xsplmin)+" "+str(ysplmin)+ "))"
			      fet = QgsFeature()
			      pr= gridtmp.dataProvider()
			      fet.setGeometry(QgsGeometry.fromWkt(pol))
			      pr.addFeatures( [ fet ] )
			      gridtmp.commitChanges()
			      #write it to tempfile
			      writer = QgsVectorFileWriter.writeAsVectorFormat(gridtmp, tempfile,"utf-8",crs,"ESRI Shapefile")
			      folder= outputfolder + os.sep + str(i)+os.sep + str(j)+ os.sep
			      if not os.path.exists(folder):
				os.makedirs(folder)
	      
			      processing.runalg('qgis:intersection', rastermap, tempfile , folder+ pref +str(i)+"_"+str(j)+".shp")

			      if self.dlg.addTiles.isChecked()== True:
				layer = QgsVectorLayer(folder+ pref +str(i)+"_"+str(j)+".shp" , pref +str(i)+"_"+str(j), "ogr")
				QgsMapLayerRegistry.instance().addMapLayer(layer)
				
			      #clean up
			      QgsMapLayerRegistry.instance().removeMapLayers( [gridtmp.id()] )
			      if os.path.isfile(tempfile):
				QgsVectorFileWriter.deleteShapeFile(tempfile)           
			else:
			  QMessageBox.information(None, "Grid Splitter", "Unknown file format. Only Raster and Vector are supported")
		  else:
		    QMessageBox.information(None, "Grid Splitter", "Please specify temporary file")
		
	     else:
		QMessageBox.information(None, "Grid Splitter", "Please specify output directory")
		
	    else:
	      QMessageBox.information(None, "Grid Splitter", "Please specify raster")
	      
	  else:
	    chekk="1" #end loop on "cancel button"
	    
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
        locale_path = os.path.join(self.plugin_dir,'i18n','gridSplitter_{}.qm'.format(locale))

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
        add_to_toolbar=False,
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


    def checkempties(self):
        #check if some inputs aren't valid
        outputfolder = self.dlg.OuptDir.text()
        layertocut = self.dlg.inputRasterBox.currentLayer()
        tempfile = self.dlg.tempFile.text()
        if layertocut!= "":
            if outputfolder!="":
                if tempfile !="":
                    if tempfile.upper().endswith(".SHP"):
                        pass
                    else: 
                        tempfile= tempfile + ".shp"
                    if os.path.isfile(tempfile) == True:
                        QMessageBox.information(None,"Shapefile exists!", "Please specify a shapefile that doesn't exist. The shapefile will be overwritten and deleted")
                        return "0"
                    else: 
                        if self.dlg.cutLayerRadio.isChecked(): #check for "cutlayer if this is the option
                            cutlayer = self.dlg.cutLayerBox.currentLayer()
                            if cutlayer != "": #check if cutlayer exists
                                return "1"
                            else: #if cutlayer does not exist
                                QMessageBox.information(None,"No cut layer!", "Please specify a cut layer")
                                return "0" 
                        else: 
                            return "1"
                else:
                    QMessageBox.information(None, "Grid Splitter", "Please specify temporary file")
                    return "0"
            else:
                QMessageBox.information(None, "Grid Splitter", "Please specify output directory")
                return "0"
        else:
            QMessageBox.information(None, "Grid Splitter", "Please specify layer")
            return "0"


    def run(self):
     # show the dialog
     #loop the GUI until each required parameter is checked
     chekk="0"
     while chekk != "1": 
        self.dlg.show() # Run the dialog event loop
        result = self.dlg.exec_()
        #if okay pressed, check for parameters
        if result: #if okay is pressed
            chekk = self.checkempties() #check parameters
            if chekk=="1":
                self.operate()
        else:
            chekk = "1" #end check loop and stop running
        
    
    def operate(self):
        
        #get variables
        
        outputfolder = self.dlg.OuptDir.text()
        splicesX = int(self.dlg.splicesXSpinBox.text())
        splicesY = int(self.dlg.splicesYSpinBox.text())
        tilesizeX= float(self.dlg.tileSizeX.value())
        tilesizeY= float(self.dlg.tileSizeY.value())
        layertocut = self.dlg.inputRasterBox.currentLayer()
        self.tempfile = self.dlg.tempFile.text()
        pref = self.dlg.prefixx.text()
        self.crs= layertocut.crs()   
        ext = layertocut.extent()
        cutlayer = self.dlg.cutLayerBox.currentLayer()
        
        if self.dlg.cutLayerRadio.isChecked(): #option: cut by Cutlayer
            if not os.path.exists(outputfolder):
                os.makedirs(outputfolder)
            self.amount=cutlayer.featureCount()
            goon= self.warn()
            if goon == True:
                iter = cutlayer.getFeatures()
                #do iterations over every feature
                for feature in iter:
                    i= feature.id()
                    if feature.geometry().intersects(ext):
                        self.poly = feature
                        self.temppolygon() #make temporary file
                        folder= outputfolder + os.sep + str(i)+ os.sep
                        if not os.path.exists(folder):
                            os.makedirs(folder) #make output folder
                        #run for raster layer
                        if layertocut.type()== QgsMapLayer.RasterLayer:
                            processing.runalg('gdalogr:cliprasterbymasklayer', layertocut, self.tempfile, None, False, False, "",folder +pref + str(i)+ ".tif")
                            
                            if self.dlg.addTiles.isChecked()== True:  
                                #add raster layer to canvas
                                fileInfo = QFileInfo(folder +pref + str(i)+".tif")
                                baseName = fileInfo.baseName()
                                layer = QgsRasterLayer(folder +pref + str(i)+".tif", baseName)
                                QgsMapLayerRegistry.instance().addMapLayer(layer)
                        #run for vector layer
                        else:
                            if layertocut.type()== QgsMapLayer.VectorLayer:
                            
                                processing.runalg('qgis:intersection', layertocut, self.gridtmp , folder+ pref +str(i)+".shp")
                                
                                if self.dlg.addTiles.isChecked()== True:
                                    layer = QgsVectorLayer(folder+ pref +str(i)+".shp" , pref +str(i), "ogr")
                                    QgsMapLayerRegistry.instance().addMapLayer(layer)
                    
                        self.cleanup()#clean up tempfile
            else: #goon == false
                pass
        else: #option:cut by tile
            if not os.path.exists(outputfolder):
                os.makedirs(outputfolder) #make output base directory
            xmax = float(layertocut.extent().xMaximum())
            xmin = float(layertocut.extent().xMinimum())
            ymax = float(layertocut.extent().yMaximum())
            ymin = float(layertocut.extent().yMinimum())
            if layertocut.type()== QgsMapLayer.RasterLayer: #option cutbytile, raster layer
                 #if raster layer, get extents and calculate so it doesn't cut pixels. 
                 #Make the tiles up to one pixel larger if they cut
                rwidth = layertocut.width()
                rheight = layertocut.height()
                xres = (xmax-xmin)/rwidth
                yres = (ymax-ymin)/rheight
                #if tile number is given
                if self.dlg.numberTilesRadio.isChecked():
                    ixx= float(rwidth)/splicesX
                    iyy= float(rheight)/splicesY
                    xsplice = math.ceil(ixx) * xres
                    ysplice = math.ceil(iyy) * yres
                else:
                    #if tile size is given
                    if self.dlg.tileSizeRadio.isChecked():
                        #snap tilesize up to resolution
                        xsplice = math.ceil(float(tilesizeX)/xres) * xres  
                        ysplice = math.ceil(float(tilesizeY)/yres) * yres
                        splicesX = int(math.ceil((xmax -xmin)/ float(xsplice)))
                        splicesY = int(math.ceil((ymax -ymin)/ float(ysplice)))
                self.amount = splicesX * splicesY    
                goon = self.warn()    
                if goon == True:    
                    #iterate
                    for i in range(splicesX):
                        for j in range(splicesY):
                            
                            #make a temporary Polygon
                            xsplmin= xmin + i*xsplice
                            xsplmax= xmin + (i+1)*xsplice
                            ysplmin= ymin + j*ysplice
                            ysplmax = ymin + (j+1)*ysplice
                            pol= "POLYGON (("+str(xsplmin)+" "+str(ysplmin)+", "+str(xsplmax)+" "+str(ysplmin)+", "+str(xsplmax)+" "+str(ysplmax)+", "+str(xsplmin)+" "+str(ysplmax)+", "+str(xsplmin)+" "+str(ysplmin)+ "))"
                            self.poly = QgsFeature()
                            self.poly.setGeometry(QgsGeometry.fromWkt(pol))
                            self.temppolygon()
                            
                            folder= outputfolder + os.sep + str(i)+os.sep + str(j)+ os.sep 
                            if not os.path.exists(folder): #create folders
                                os.makedirs(folder)
                            processing.runalg('gdalogr:cliprasterbymasklayer', layertocut, self.tempfile , None, False, False, "",folder +pref + str(i)+"_"+str(j)+".tif")
                            
                            #add raster layer to canvas
                            if self.dlg.addTiles.isChecked()== True:
                                fileInfo = QFileInfo(folder +pref + str(i)+"_"+str(j)+".tif")
                                baseName = fileInfo.baseName()
                                layer = QgsRasterLayer(folder +pref + str(i)+"_"+str(j)+".tif", baseName)
                                QgsMapLayerRegistry.instance().addMapLayer(layer)
                                
                            #clean up
                            self.cleanup()
                else: #goon == false
                    pass
                    
            else: #option cut by tile, vector layer
                if layertocut.type()== QgsMapLayer.VectorLayer:
                    
                    if self.dlg.numberTilesRadio.isChecked():#if tile number is given
                        xsplice = (xmax - xmin)/splicesX
                        ysplice = (ymax - ymin)/splicesY
                    else: #if tile size is given
                        
                        if self.dlg.tileSizeRadio.isChecked():
                            xsplice = tilesizeX
                            ysplice = tilesizeY
                            splicesX = int(math.ceil((xmax-xmin)/float(tilesizeX)))
                            splicesY = int(math.ceil((ymax-ymin)/float(tilesizeY)))
                    
                    self.amount = splicesX*splicesY
                    goon = self.warn()
                    if goon==True:
                        #iterate
                        for i in range(splicesX):
                            for j in range(splicesY):
                                #make a temporary polygon
                                xsplmin= xmin + i*xsplice
                                xsplmax= xmin + (i+1)*xsplice
                                ysplmin= ymin + j*ysplice
                                ysplmax = ymin + (j+1)*ysplice
                                pol= "POLYGON (("+str(xsplmin)+" "+str(ysplmin)+", "+str(xsplmax)+" "+str(ysplmin)+", "+str(xsplmax)+" "+str(ysplmax)+", "+str(xsplmin)+" "+str(ysplmax)+", "+str(xsplmin)+" "+str(ysplmin)+ "))"
                                self.poly = QgsFeature()
                                self.poly.setGeometry(QgsGeometry.fromWkt(pol))
                                self.temppolygon()
                                
                                folder= outputfolder + os.sep + str(i)+os.sep + str(j)+ os.sep
                                if not os.path.exists(folder):
                                    os.makedirs(folder) #make folders
                                    
                                processing.runalg('qgis:intersection', layertocut, self.gridtmp , folder+ pref +str(i)+"_"+str(j)+".shp")
                                
                                #add to canvas
                                if self.dlg.addTiles.isChecked()== True:
                                    layer = QgsVectorLayer(folder+ pref +str(i)+"_"+str(j)+".shp" , pref +str(i)+"_"+str(j), "ogr")
                                    QgsMapLayerRegistry.instance().addMapLayer(layer)
                                
                                #clean up
                                self.cleanup()
                    else:
                        pass
                        
    def cleanup(self):
        QgsMapLayerRegistry.instance().removeMapLayers( [self.gridtmp.id()] )
        if os.path.isfile(self.tempfile):
            QgsVectorFileWriter.deleteShapeFile(self.tempfile)
            
    def temppolygon(self):
        #stop the annoying asks with user-defined CRS
        if self.crs.authid().startswith('USER'):
            epsg = self.crs.toWkt()
        else:
            epsg= self.crs.authid() 
        tmpf= "Polygon?crs="+ epsg #what happens if there's no EPSG?
        self.gridtmp = QgsVectorLayer(tmpf, "gridtile", "memory")
        QgsMapLayerRegistry.instance().addMapLayer(self.gridtmp)
        self.gridtmp.startEditing()
        fet = QgsFeature()
        pr= self.gridtmp.dataProvider()
        fet.setGeometry(self.poly.geometry())
        pr.addFeatures( [ fet ] )
        self.gridtmp.commitChanges()
        #write it to tempfile
        QgsVectorFileWriter.writeAsVectorFormat(self.gridtmp, self.tempfile,"utf-8",self.crs,"ESRI Shapefile")
        
    def warn(self):
        message= "you are about to make " + str(self.amount) + " tiles. Continue?"
        k = QMessageBox .question(None, "Grid Splitter", message, QMessageBox.Yes, QMessageBox.Abort)
        if k == QMessageBox.Yes:
            return True
        else:
            return False
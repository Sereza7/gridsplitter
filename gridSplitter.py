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
import tempfile #for temp shapefile naming


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


    def checkempties(self):
        #check if some inputs aren't valid
        outputfolder = self.dlg.OuptDir.text()
        index = self.dlg.inputRasterBox.currentIndex()
        layertocut = self.dlg.inputRasterBox.itemData(index)
        if layertocut!= "":
            if outputfolder!="":
                if self.dlg.cutLayerRadio.isChecked(): #check for cutlayer if this is the option
                    index = self.dlg.cutLayerBox.currentIndex()
                    self.cutlayer = self.dlg.cutLayerBox.itemData(index)
                    if self.cutlayer != "": #check if cutlayer exists
                        return "1"
                    else: #if cutlayer does not exist
                        QMessageBox.information(None,"No cut layer!", "Please specify a cut layer")
                        return "0" 
                else: 
                    return "1"
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
     #fill layers:
     layers = QgsMapLayerRegistry.instance().mapLayers().values()
     for layer in layers:
        if layer.type() == QgsMapLayer.VectorLayer and layer.geometryType() == QGis.Polygon:
             self.dlg.cutLayerBox.addItem( layer.name(), layer ) 
        #if it is a valid filename, add
        self.dlg.inputRasterBox.addItem(layer.name(), layer)
        
     while chekk != "1": 
        self.dlg.show() #0 Run the dialog event loop
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
        index = self.dlg.inputRasterBox.currentIndex()
        layertocut = self.dlg.inputRasterBox.itemData(index)
        #get a temp file name. Process should be less ugly
        tmpc, self.temp = tempfile.mkstemp(suffix='.shp', prefix='gridSplitter_tmpfile_')
        os.close(tmpc)
        os.remove(self.temp)
        pref = self.dlg.prefixx.text()
        self.layertocutcrs= layertocut.crs()   
        ext = layertocut.extent()
        l = layertocut.dataProvider().dataSourceUri()
        layertocutFilePath= l.split('|')[0]
        existwarning=0
        
        if self.dlg.cutLayerRadio.isChecked(): #option: cut by Cutlayer
            if not os.path.exists(outputfolder):
                os.makedirs(outputfolder)
            self.amount=self.cutlayer.featureCount()
            goon= self.warn()
            if goon == True:
                if self.layertocutcrs != self.cutlayer.crs():
                    self.reprojectTempFile()
                else:
                    self.epsg=self.layertocutcrs.toProj4()
                #do iterations over every feature
                iter = self.cutlayer.getFeatures() 
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
                            nodata = layertocut.dataProvider().srcNoDataValue(1) #what about multiband rasters?
                            self.epsg=self.layertocutcrs.toProj4()
                            
                            #TODO calling gdalwarp directly? solves problem with "unprojected" jpg etc., but is OS dependent?
                            newfile = folder+pref+str(i)+".tif"
                            if os.path.isfile(newfile): #warn if file exists. But only warn once in big runs
                                if existwarning == 0:
                                    existwarning = self.exists()
                            #call(["gdalwarp","-q","-s_srs",self.epsg, "-t_srs",self.epsg, "-cblend", "1", "-crop_to_cutline","-srcnodata",str(nodata),"-dstnodata",str(nodata),"-cutline",self.temp,layertocutFilePath,newfile])
                            processing.runalg('gdalogr:cliprasterbymasklayer', layertocut, self.temp, None, False, False, "-cblend 1", folder +pref + str(i)+ ".tif")
                            if self.dlg.addTiles.isChecked()== True:  
                                #add raster layer to canvas
                                fileInfo = QFileInfo(folder +pref + str(i)+".tif")
                                baseName = fileInfo.baseName()
                                layer = QgsRasterLayer(folder +pref + str(i)+".tif", baseName)
                                QgsMapLayerRegistry.instance().addMapLayer(layer)
                        
                        else: #run for vector layer
                            if layertocut.type()== QgsMapLayer.VectorLayer:
                                
                                #TODO Experimental: Call ogr directly
                                #	ogr2ogr  -clipsrc  testpolygon1.shp  output.shp            testpolygon2.shp
                                newfile=folder+ pref +str(i)+".shp"
                                if os.path.isfile(newfile): #warn if file exists. But only warn once in big runs
                                    if existwarning == 0:
                                        existwarning = self.exists()
                                #call(["ogr2ogr","-t_srs",self.epsg,"-s_srs",self.epsg,"-clipsrc" ,self.temp, newfile, layertocutFilePath])
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
            self.epsg=self.layertocutcrs.toProj4()
            xmax = float(layertocut.extent().xMaximum())
            xmin = float(layertocut.extent().xMinimum())
            ymax = float(layertocut.extent().yMaximum())
            ymin = float(layertocut.extent().yMinimum())
            if layertocut.type()== QgsMapLayer.RasterLayer: #option cutbytile, raster layer
                 #if raster layer, get extents and calculate so it doesn't cut pixels. 
                 #Make the tiles up to one pixel larger if they cut
                rwidth = float(layertocut.width())
                rheight = float(layertocut.height())
                xres = (xmax-xmin)/rwidth #WMS layer fails here: ZeroDivisionError: float division by zero
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
                            nodata = layertocut.dataProvider().srcNoDataValue(1) #what about multiband rasters?
                            newfile = folder+pref+str(i)+"_"+str(j)+".tif"
                            if os.path.isfile(newfile): #warn if file exists. But only warn once in big runs
                                if existwarning == 0:
                                    existwarning = self.exists()
                            #TODO experimental
                            #call(["gdalwarp","-q","-s_srs",self.epsg, "-t_srs",self.epsg, "-crop_to_cutline","-srcnodata",str(nodata),"-dstnodata",str(nodata),"-cutline",self.temp,layertocutFilePath,newfile])
                            processing.runalg('gdalogr:cliprasterbymasklayer', layertocut, self.temp , None, False, False, "",folder +pref + str(i)+"_"+str(j)+".tif")
                            
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
                                #TODO Experimental: call ogr directly instead of qgis    
                                newfile = folder+ pref +str(i)+"_"+str(j)+".shp"
                                if os.path.isfile(newfile): #warn if file exists. But only warn once in big runs
                                    if existwarning == 0:
                                        existwarning = self.exists()
                                #call(["ogr2ogr","-t_srs",self.epsg,"-s_srs",self.epsg,"-clipsrc",self.temp, newfile, layertocutFilePath])
                                processing.runalg('qgis:intersection', layertocut, self.temp , folder+ pref +str(i)+"_"+str(j)+".shp")
                                
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
        cpg = self.temp[:-4]+ ".cpg"
        if os.path.isfile(cpg):
            os.remove(cpg)
            
    def temppolygon(self):
        #delete tempfile. windows won't overwrite it
        if os.path.isfile(self.temp):
            os.remove(self.temp)
        if os.path.isfile(self.temp):
            QgsVectorFileWriter.deleteShapeFile(self.temp)
        #stop the annoying asks with user-defined CRS
        if self.layertocutcrs.authid().startswith('USER'):
            self.epsg = self.layertocutcrs.toWkt()
        else:
            self.epsg= self.layertocutcrs.authid() 
        tmpf= "Polygon?crs="+ self.epsg
        self.gridtmp = QgsVectorLayer(tmpf, "gridtile", "memory")
        QgsMapLayerRegistry.instance().addMapLayer(self.gridtmp)
        self.gridtmp.startEditing()
        fet = QgsFeature()
        pr= self.gridtmp.dataProvider()
        fet.setGeometry(self.poly.geometry())
        pr.addFeatures( [ fet ] )
        self.gridtmp.commitChanges()
        #create tempfile, write stuff in it
        writer = QgsVectorFileWriter.writeAsVectorFormat(self.gridtmp, self.temp,"utf-8",self.layertocutcrs,"ESRI Shapefile")
        #close tempfile, unlock it. Windows 7 demands it, else it will reuse the same polygon over and over
        del writer
    
    def warn(self):
        message= "you are about to make up to " + str(self.amount) + " tiles. Continue?"
        k = QMessageBox .question(None, "Grid Splitter", message, QMessageBox.Yes, QMessageBox.Abort)
        if k == QMessageBox.Yes:
            return True
        else:
            return False

    def reprojectTempFile(self):
        #reproject cutlayer into temporary memory layer
        message= "The Cutlayer doesn't match the projection of the layer to be cut. Should I try to reproject (temporary file)?"
        k = QMessageBox .question(None, "Grid Splitter", message, QMessageBox.Yes, QMessageBox.No)
        if k == QMessageBox.Yes:
            if self.layertocutcrs.authid().startswith('USER'): #user-defined CRS
                self.epsg = self.layertocutcrs.toWkt()
            else: #EPSG - defined				
                self.epsg= self.layertocutcrs.authid()
            cutlayersrs= self.cutlayer.crs()
            if cutlayersrs.authid().startswith('USER'): #user-defined CRS
                srcsrs = cutlayersrs.toWkt()
            else:				#EPSG - defined
                srcsrs= cutlayersrs.authid()
            #reproject TODO with ogr2ogr
            tmpc, tmp = tempfile.mkstemp(suffix='.shp', prefix='gridSplitter_tmpfile_')
            os.close(tmpc)
            os.remove(tmp)
            c = self.cutlayer.dataProvider().dataSourceUri()
            cutlayername= c.split('|')[0]
            #call(["ogr2ogr","-t_srs",self.epsg,"-s_srs",srcsrs, tmp, cutlayername])
            #self.cutlayer = QgsVectorLayer(tmp,"reprojected Cutlayer","ogr")
            new= processing.runalg('qgis:reprojectlayer', self.cutlayer, self.epsg, None)
            self.cutlayer = QgsVectorLayer(new.get("OUTPUT"),"reprojected Cutlayer","ogr")
            QgsMapLayerRegistry.instance().addMapLayer(self.cutlayer)
        else: #don't reproject
            pass

    def exists(self):
      QMessageBox.information(None, "File exists", "Some output files already exist. gridSplitter does not overwrite files, so results may be unexpected")
      return 1
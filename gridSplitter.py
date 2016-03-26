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
from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, 
from PyQt4.QtCore import QFileInfo, QVariant
from PyQt4.QtGui import QAction, QIcon, QMessageBox
import resources_rc
from gridSplitter_dialog import gridSplitterDialog
from qgis.core import * 
import os, os.path, processing, math, time, tempfile, sys
from subprocess import call, CalledProcessError, check_output, PIPE, Popen
from glob import glob

class gridSplitter:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(self.plugin_dir,'i18n',
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
        self.toolbar = self.iface.addToolBar(u'gridSplitter')
        self.toolbar.setObjectName(u'gridSplitter')

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
        """check if some inputs aren't valid"""
        self.of = self.dlg.OuptDir.text()
        index = self.dlg.inputRasterBox.currentIndex()
        layertocut = self.dlg.inputRasterBox.itemData(index)
        if layertocut== "":
            QMessageBox.information(None, "Grid Splitter",
                                    self.tr("Please specify layer"))
            return 0
        
        if self.of=="":
            QMessageBox.information(None, "Grid Splitter", 
                                    self.tr("Please specify output directory"))
                return 0
                
        if self.dlg.cutLayerRadio.isChecked(): 
            index = self.dlg.cutLayerBox.currentIndex()
            self.cutlayer = self.dlg.cutLayerBox.itemData(index)
            if self.cutlayer == "": #check if cutlayer exists
                QMessageBox.information(None,self.tr("No cut layer!"),
                                        self.tr("Please specify a cut layer"))
                        return 0 
        return 1
            


    def run(self):
     
     chekk=0
     #get gdal_path if windows , else just check in current path
     if os.name=="nt" or sys.platform == "darwin":
         self.gdalprefix = QgsApplication.prefixPath()+ '/../../bin/'
     else:
        self.gdalprefix = ""
     #checking once if GDAL exists
     #TODO check with different paths, e.g QgsApplication.prefixPath()+'/bin'
     self.gdalexists= self.checkgdal()
     
     #fill layers:
     self.dlg.cutLayerBox.clear()
     self.dlg.inputRasterBox.clear()
     layers = QgsMapLayerRegistry.instance().mapLayers().values()
     for layer in layers:
         try:
             if layer.dataProvider().description().startswith('GDAL') or
             layer.dataProvider().description().startswith('OGR'): 
                if layer.type() == QgsMapLayer.VectorLayer and 
                layer.geometryType() == 2:
                    self.dlg.cutLayerBox.addItem( layer.name(), layer ) 
                self.dlg.inputRasterBox.addItem(layer.name(), layer)
         except AttributeError:
             pass
         
     result = self.dlg.exec_()
     
     while result: #if okay is pressed
            chekk = self.checkempties() #check parameters
            if chekk==1:
                self.operate()
            else:
                result = self.dlg.exec_()
            
    def operate(self):
        #activate logging
        self.efn= tempfile.gettempdir() + os.sep + "gridsplitter-error.log"
        self.ef= os.open(self.efn,os.O_APPEND|os.O_CREAT|os.O_RDWR)
        self.lfn= tempfile.gettempdir() + os.sep + "gridsplitter-log.log"
        self.lf= os.open(self.lfn,os.O_APPEND|os.O_CREAT|os.O_RDWR)
        #get variables
        self.of = self.dlg.OuptDir.text()
        splicesX = int(self.dlg.splicesXSpinBox.text())
        splicesY = int(self.dlg.splicesYSpinBox.text())
        tilesizeX= float(self.dlg.tileSizeX.value())
        tilesizeY= float(self.dlg.tileSizeY.value())
        index = self.dlg.inputRasterBox.currentIndex()
        layertocut = self.dlg.inputRasterBox.itemData(index)
        pref = self.dlg.prefixx.text()
        self.layertocutcrs= layertocut.crs()   
        ext = layertocut.extent()
        l = layertocut.dataProvider().dataSourceUri()
        lyrct_fp= l.split('|')[0]
        existwarning=0
        self.existerror=0
        self.subpath = 0
                        
        if self.dlg.cutLayerRadio.isChecked(): #option: cut by Cutlayer
            if not os.path.exists(self.of):
                os.makedirs(self.of)
            self.amount=self.cutlayer.featureCount()
            goon= self.warn()
            if goon == False:
                return
            else:
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
                        self.temppolygon() 
                        if self.dlg.subfolderRadio.isChecked():
                            folder= self.of + os.sep + str('%04d' %(i))+ os.sep
                            if not os.path.exists(folder):
                                os.makedirs(folder)
                                self.subpath=1
                        if self.dlg.nosubfolderRadio.isChecked():
                            folder = self.of+os.sep
                            self.subpath=0
                            
                        #run for raster layer
                        if layertocut.type()== QgsMapLayer.RasterLayer:
                            nodata = layertocut.dataProvider().srcNoDataValue(1)
                            #TODO nadata values for other bands different?
                            self.epsg=self.layertocutcrs.toProj4()
                            newfile = folder+pref+str('%04d' %(i))+".tif"
                            if os.path.isfile(newfile): 
                                if existwarning == 0:
                                    existwarning = self.exists()
                            if self.gdalexists==True:
                                self.Popenargs=[self.gdalprefix+"gdalwarp",
                                                "-q",
                                                "-s_srs", self.epsg, 
                                                "-t_srs", self.epsg, 
                                                "-wo","CUTLINE_ALL_TOUCHED=TRUE",
                                                "-crop_to_cutline",
                                                "-srcnodata", (nodata),
                                                "-dstnodata",str(nodata),
                                                "-cutline",self.temp,lyrct_fp,
                                                newfile]
                                errx= self.runPopen()
                                if errx==1:
                                    self.errmsg = "this error was created by "
                                    +"gdalwarp at " 
                                    + time.strftime('%X %x %Z')
                                    self.errorlog()
                            else:
                                k= processing.runalg('gdalogr:cliprasterbymasklayer',
                                                     layertocut, 
                                                     self.temp,nodata, 
                                                     False, 
                                                     False,
                                                     "-wo CUTLINE_ALL_TOUCHED=TRUE", 
                                                     folder +pref + str('%04d' %(i))+ ".tif")
                                del k
                            if self.dlg.addTiles.isChecked()== True:
                                #add raster layer to canvas
                                fileInfo = QFileInfo(folder +pref + str('%04d' %(i))+".tif")
                                baseName = fileInfo.baseName()
                                layer = QgsRasterLayer(folder +pref + str('%04d' %(i))+".tif", 
                                                       baseName)
                                QgsMapLayerRegistry.instance().addMapLayer(layer)
                        
                        else: #run for vector layer
                            if layertocut.type()== QgsMapLayer.VectorLayer:
                                
                                newfile=folder+ pref +str('%04d' %(i))+".shp"
                                if os.path.isfile(newfile):
                                    if existwarning == 0:
                                        existwarning = self.exists()
                                if self.gdalexists ==True:
                                    self.Popenargs=[self.gdalprefix+"ogr2ogr",
                                                    "-t_srs",self.epsg,
                                                    "-s_srs",self.epsg,
                                                    "-clipsrc" ,self.temp, 
                                                    newfile, 
                                                    lyrct_fp]
                                    errx=self.runPopen()
                                    if errx==1:
                                        self.errmsg = "this error was created" 
                                        +" by ogr2ogr at " 
                                        + time.strftime('%X %x %Z')
                                        self.errorlog() 
                                else:
                                    k= processing.runalg('qgis:intersection', 
                                                         layertocut, 
                                                         self.gridtmp , 
                                                         folder+ pref +str('%04d' %(i))+".shp")
                                    del k
                                if self.dlg.addTiles.isChecked()== True:
                                    layer = QgsVectorLayer(
                                        folder+ pref +str('%04d' %(i))+".shp" ,
                                        pref + str('%04d' %(i)), "ogr")
                                    QgsMapLayerRegistry.instance().addMapLayer(layer)
                    
                        self.cleanup()
                self.tileindex()
            
        else: #option:cut by tile
            if not os.path.exists(self.of):
                os.makedirs(self.of) 
            self.epsg=self.layertocutcrs.toProj4()
            xmax = float(layertocut.extent().xMaximum())
            xmin = float(layertocut.extent().xMinimum())
            ymax = float(layertocut.extent().yMaximum())
            ymin = float(layertocut.extent().yMinimum())
            if layertocut.type()== QgsMapLayer.RasterLayer: 
                #option cutbytile, raster layer
                rwidth = float(layertocut.width())
                rheight = float(layertocut.height())
                xres = (xmax-xmin)/rwidth 
                yres = (ymax-ymin)/rheight
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
                            pol= "POLYGON (("+str(xsplmin)
                            +" "+str(ysplmin)+", "+str(xsplmax)+" "
                            +str(ysplmin)+", "+str(xsplmax)+" "
                            +str(ysplmax)+", "+str(xsplmin)+" "
                            +str(ysplmax)+", "+str(xsplmin)+" 
                            "+str(ysplmin)+ "))"
                            
                            self.poly = QgsFeature()
                            self.poly.setGeometry(QgsGeometry.fromWkt(pol))
                            self.temppolygon()
                            
                            if self.dlg.subfolderRadio.isChecked():
                                folder= self.of + os.sep 
                                + str('%04d' %(i))+os.sep 
                                + str('%04d' %(j))+ os.sep 
                                if not os.path.exists(folder): 
                                    os.makedirs(folder)
                                self.subpath=2
                            if self.dlg.nosubfolderRadio.isChecked():
                                folder = self.of+os.sep
                                self.subpath=0
                            nodata = layertocut.dataProvider().srcNoDataValue(1)
                            newfile = folder
                            +pref
                            +str('%04d' %(i))+"_"+str('%04d' %(j))+".tif"
                            if os.path.isfile(newfile):
                                if existwarning == 0:
                                    existwarning = self.exists()
                            if self.gdalexists ==True:
                                self.Popenargs=[self.gdalprefix+"gdalwarp",
                                                "-q",
                                                "-s_srs",self.epsg, 
                                                "-t_srs",self.epsg, 
                                                "-crop_to_cutline",
                                                "-srcnodata",str(nodata),
                                                "-dstnodata",str(nodata),
                                                "-cutline",self.temp,
                                                lyrct_fp,newfile]
                                errx=self.runPopen()
                                if errx==1:
                                    self.errmsg = "this error was created by "
                                    +"gdalwarp at " + time.strftime('%X %x %Z')
                                    self.errorlog()
                            else:
                                k= processing.runalg('gdalogr:cliprasterbymasklayer', 
                                                     layertocut, 
                                                     self.temp , 
                                                     nodata, 
                                                     False, 
                                                     False, 
                                                     "",
                                                     folder +pref 
                                                     + str('%04d' %(i))
                                                     +"_"+str('%04d' %(j))+".tif")
                                del k
                            #add raster layer to canvas
                            if self.dlg.addTiles.isChecked()== True:
                                fileInfo = QFileInfo(folder 
                                                     +pref 
                                                     + str('%04d' %(i))
                                                     +"_"+str('%04d' %(j))+".tif")
                                baseName = fileInfo.baseName()
                                layer = QgsRasterLayer(folder +pref 
                                                       + str('%04d' %(i))+"_"
                                                       +str('%04d' %(j))+".tif", 
                                                       baseName)
                                QgsMapLayerRegistry.instance().addMapLayer(layer)
                            
                            self.cleanup()
                    self.tileindex()
            else: #option cut by tile, vector layer
                if layertocut.type()== QgsMapLayer.VectorLayer:
                    
                    if self.dlg.numberTilesRadio.isChecked():
                        xsplice = (xmax - xmin)/splicesX
                        ysplice = (ymax - ymin)/splicesY
                    else: #if tile size is given
                        if self.dlg.tileSizeRadio.isChecked():
                            xsplice = tilesizeX
                            ysplice = tilesizeY
                            splicesX = int(math.ceil((xmax-xmin)/
                                                     float(tilesizeX)))
                            splicesY = int(math.ceil((ymax-ymin)/
                                                     float(tilesizeY)))
                    
                    self.amount = splicesX*splicesY
                    goon = self.warn()
                    if goon==True:
                        #iterate
                        for i in range(splicesX):
                            for j in range(splicesY):
                                xsplmin= xmin + i*xsplice
                                xsplmax= xmin + (i+1)*xsplice
                                ysplmin= ymin + j*ysplice
                                ysplmax = ymin + (j+1)*ysplice
                                pol= "POLYGON (("+str(xsplmin)+" "
                                +str(ysplmin)+", "+str(xsplmax)+" "
                                +str(ysplmin)+", "+str(xsplmax)+" "
                                +str(ysplmax)+", "+str(xsplmin)+" "
                                +str(ysplmax)+", "+str(xsplmin)+" "
                                +str(ysplmin)+ "))"
                                self.poly = QgsFeature()
                                self.poly.setGeometry(QgsGeometry.fromWkt(pol))
                                self.temppolygon()
                                
                                if self.dlg.subfolderRadio.isChecked():
                                    folder= self.of + os.sep 
                                    + str('%04d' %(i))+os.sep 
                                    + str('%04d' %(j))+ os.sep
                                    if not os.path.exists(folder):
                                        os.makedirs(folder) #make folders
                                    self.subpath=2
                                if self.dlg.nosubfolderRadio.isChecked():
                                    folder= self.of+os.sep
                                    self.subpath=0
                                newfile = folder+ pref +str('%04d' %(i))
                                +"_"+str('%04d' %(j))+".shp"
                                if os.path.isfile(newfile):
                                    if existwarning == 0:
                                        existwarning = self.exists()
                                if self.gdalexists==True:
                                    self.Popenargs=[self.gdalprefix+"ogr2ogr",
                                                    "-t_srs",self.epsg,
                                                    "-s_srs",self.epsg,
                                                    "-clipsrc",self.temp, 
                                                    newfile, lyrct_fp]
                                    errx=self.runPopen()
                                    if errx==1:
                                        self.errmsg = "this error was created"
                                        + "by ogr2ogr at " 
                                        + time.strftime('%X %x %Z')
                                        self.errorlog()
                                else: 
                                    k= processing.runalg('qgis:intersection', 
                                                         layertocut, 
                                                         self.temp , 
                                                         folder+ pref 
                                                         +str('%04d' %(i))
                                                         +"_"+ str('%04d' %(j))
                                                         +".shp")
                                    del k
                                if self.dlg.addTiles.isChecked()== True:
                                    layer = QgsVectorLayer(folder
                                                           + pref 
                                                           +str('%04d' %(i))+"_"
                                                           +str('%04d' %(j))
                                                           +".shp", 
                                                           pref 
                                                           +str('%04d' %(i))+"_"
                                                           +str('%04d' %(j)), 
                                                           "ogr")
                                    QgsMapLayerRegistry.instance().addMapLayer(layer)
                                self.cleanup()
                        self.tileindex()
        os.close(self.ef)
        os.close(self.lf)
        
        
    def cleanup(self):
        #does not work on win7. runalg keeps them open
        if os.path.isfile(self.temp): 
            QgsVectorFileWriter.deleteShapeFile(self.temp)
        cpg = self.temp[:-4]+ ".cpg"
        if os.path.isfile(cpg):
            os.remove(cpg)
            
    def temppolygon(self):
        self.epsg = self.layertocutcrs.toWkt()
        tmpf= "Polygon?crs="+ self.epsg
        self.gridtmp = QgsVectorLayer(tmpf, "gridtile", "memory")
        self.gridtmp.startEditing()
        fet = QgsFeature()
        pr= self.gridtmp.dataProvider()
        fet.setGeometry(self.poly.geometry())
        pr.addFeatures( [ fet ] )
        self.gridtmp.commitChanges()
        tmpc, self.temp = tempfile.mkstemp(suffix='.shp', 
                                           prefix='gridSplitter_tmpfile_')
        os.close(tmpc)
        os.remove(self.temp)
        writer = QgsVectorFileWriter.writeAsVectorFormat(self.gridtmp, 
                                                         self.temp,
                                                         "utf-8",
                                                         self.layertocutcrs,
                                                         "ESRI Shapefile")
        del writer
        
    def warn(self):
        message= self.tr("you are about to make up to ") 
        + str(self.amount) + self.tr(" tiles. Continue?")
        k = QMessageBox .question(None, "Grid Splitter", 
                                  message, 
                                  QMessageBox.Yes, 
                                  QMessageBox.Abort)
        if k == QMessageBox.Yes:
            return True
        else:
            return False

    def reprojectTempFile(self):
        message= self.tr("The Cutlayer doesn't match the projection of the"
                         +"layer to be cut. Should I try to reproject"
                         + "(temporary file)?")
        k = QMessageBox .question(None, 
                                  "Grid Splitter", 
                                  message, 
                                  QMessageBox.Yes, 
                                  QMessageBox.No)
        if k == QMessageBox.Yes:
            self.epsg = self.layertocutcrs.toProj4()
            cutlayersrs= self.cutlayer.crs()
            srcsrs = cutlayersrs.toProj4()
            tmpc, tmp = tempfile.mkstemp(suffix='.shp', 
                                         prefix='gridSplitter_reprojectedlayer_')
            os.close(tmpc)
            os.remove(tmp)
            c = self.cutlayer.dataProvider().dataSourceUri()
            cutlayername= c.split('|')[0]
            if self.gdalexists==True:
                self.Popenargs=[self.gdalprefix+"ogr2ogr",
                                "-t_srs",self.epsg,
                                "-s_srs",srcsrs, 
                                tmp, cutlayername]
                errx=self.runPopen()
                self.cutlayer = QgsVectorLayer(tmp,
                                               "reprojected Cutlayer",
                                               "ogr")
                if errx==1:
                    self.errmsg = "this error was created by ogr2ogr at " 
                    + time.strftime('%X %x %Z')
                    self.errorlog()
            else:
                new= processing.runalg('qgis:reprojectlayer', 
                                       self.cutlayer, 
                                       self.epsg, 
                                       None)
                self.cutlayer = QgsVectorLayer(new.get("OUTPUT"),
                                               "reprojected Cutlayer",
                                               "ogr")
                del new
            QgsMapLayerRegistry.instance().addMapLayer(self.cutlayer)

    def exists(self):
      QMessageBox.information(None, self.tr("File exists"), 
                              self.tr("Some output files already exist."
                                  +"gridSplitter does not overwrite files,"
                                  +" so results may be unexpected"))
      return 1
      
    def checkgdal(self):
    """checks if GDALWARP is in the %Path. Assuming, ogr2ogr is there, too"""
        try: 
            call(self.gdalprefix+'gdalwarp')
        except OSError:
            return False
        else:
            return True

    def errorlog(self):
        if self.existerror == 0:
            QMessageBox.information(None, "Grid Splitter", 
                                    self.tr("There was an error executing."
                                        +" See log for additional details"))
            self.existerror = 1
        errormessage= self.errmsg + os.linesep
        os.write(self.ef, errormessage)
    
    def tileindex(self):
        if self.dlg.tileindexCheck.isChecked():
            pref= self.dlg.prefixx.text()
            path=self.of
            index = self.dlg.inputRasterBox.currentIndex()
            layertocut = self.dlg.inputRasterBox.itemData(index)
            self.epsg=layertocut.crs().toProj4()
            if layertocut.type()== QgsMapLayer.RasterLayer:
                outputsuf= ".tif"
            if layertocut.type()== QgsMapLayer.VectorLayer:
                outputsuf= ".shp"
            if self.subpath==0:
                files= glob(self.of+os.sep+pref+"*"+outputsuf)
            else:
                if self.subpath==1:
                    files= glob(self.of+os.sep+"*"+os.sep+pref+"*"+outputsuf)
                else:
                    files= glob(self.of+os.sep+"*"+os.sep+"*"
                                +os.sep+pref+"*"+outputsuf)
            
            for f1 in files:
                if layertocut.type()== QgsMapLayer.RasterLayer:
                    self.Popenargs=[self.gdalprefix+'gdaltindex', 
                                    '-t_srs',self.epsg,
                                    self.of+os.sep+pref+"tileindex.shp",
                                    f1]
                    self.runPopen()
                    if layertocut.type()== QgsMapLayer.VectorLayer: 
                        self.Popenargs=[self.gdalprefix+'ogrtindex',
                                        self.of+os.sep+pref+"tileindex.shp",
                                        f1]
                        self.runPopen()
            layer = QgsVectorLayer(self.of+os.sep+pref+"tileindex.shp" ,
                                   pref+"tileindex", "ogr")
            QgsMapLayerRegistry.instance().addMapLayer(layer)
            
            layer.dataProvider().addAttributes([QgsField("row", QVariant.String,"",10),
                                                QgsField("col",QVariant.String,"",10)])
            layer.updateFields()
            layer.startEditing()
            for feature in layer.getFeatures():
                withoutextension = feature['location'].split('.')[-2]
                withoutpath = withoutextension.split(os.sep)[-1]
                withoutprefix = withoutextension.split(self.dlg.prefixx.text())[-1]
                feature['col'] = withoutprefix.split('_')[0]
                try: 
                    feature['row'] = withoutprefix.split('_')[1]
                except IndexError:
                    pass
                layer.updateFeature(feature)
            d = layer.commitChanges()
            print d
            
    def runPopen(self):
        if os.name=="nt":
            p=Popen(self.Popenargs,
                    stdin=PIPE, 
                    stdout=self.lf,  
                    stderr=self.ef, 
                    creationflags=0x08000000)
            e=p.wait()
        else:
            p=Popen(self.Popenargs, 
                    stdin=PIPE, 
                    stdout=self.lf,  
                    stderr=self.ef)
            e=p.wait()
        return e

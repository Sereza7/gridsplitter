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
from qgis.core import * 
import os, os.path, processing, math, time
import tempfile #for temp shapefile naming
from subprocess import call, CalledProcessError, check_output
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
        self.outputfolder = self.dlg.OuptDir.text()
        index = self.dlg.inputRasterBox.currentIndex()
        layertocut = self.dlg.inputRasterBox.itemData(index)
        if layertocut!= "":
            if self.outputfolder!="":
                if self.dlg.cutLayerRadio.isChecked(): #check for cutlayer if this is the option
                    index = self.dlg.cutLayerBox.currentIndex()
                    self.cutlayer = self.dlg.cutLayerBox.itemData(index)
                    if self.cutlayer != "": #check if cutlayer exists
                        return "1"
                    else: #if cutlayer does not exist
                        QMessageBox.information(None,self.tr("No cut layer!"), self.tr("Please specify a cut layer"))
                        return "0" 
                else: 
                    return "1"
            else:
                QMessageBox.information(None, "Grid Splitter", self.tr("Please specify output directory"))
                return "0"
        else:
            QMessageBox.information(None, "Grid Splitter", self.tr("Please specify layer"))
            return "0"


    def run(self):
     #remove all old tempfiles tempdir/gridSplitter_tmpfile_* ?
     # show the dialog
     #loop the GUI until each required parameter is checked
     
     chekk="0"
     #get gdal_path if windows , else just check in current path
     if os.name=="nt":
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
         if layer.dataProvider().description().startswith('GDAL') or layer.dataProvider().description().startswith('OGR'): 
            if layer.type() == QgsMapLayer.VectorLayer and layer.geometryType() == QGis.Polygon:
                self.dlg.cutLayerBox.addItem( layer.name(), layer ) 
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
        #activate logging
        self.errorfilename= tempfile.gettempdir() + os.sep + "gridsplitter-error.log"
        self.errorfile= os.open(self.errorfilename,os.O_APPEND|os.O_CREAT|os.O_RDWR)
        #get variables
        self.outputfolder = self.dlg.OuptDir.text()
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
        layertocutFilePath= l.split('|')[0]
        existwarning=0
        self.existerror=0
                        
        if self.dlg.cutLayerRadio.isChecked(): #option: cut by Cutlayer
            if not os.path.exists(self.outputfolder):
                os.makedirs(self.outputfolder)
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
                        if self.dlg.subfolderRadio.isChecked():
                            folder= self.outputfolder + os.sep + str('%04d' %(i))+ os.sep
                            if not os.path.exists(folder):
                                os.makedirs(folder) #make output folder
                                self.subpath=1
                        if self.dlg.nosubfolderRadio.isChecked():
                            folder = self.outputfolder+os.sep
                            self.subpath=0
                        #run for raster layer
                        if layertocut.type()== QgsMapLayer.RasterLayer:
                            nodata = layertocut.dataProvider().srcNoDataValue(1) #what about multiband rasters?
                            self.epsg=self.layertocutcrs.toProj4()
                            newfile = folder+pref+str('%04d' %(i))+".tif"
                            if os.path.isfile(newfile): #warn if file exists. But only warn once in big runs
                                if existwarning == 0:
                                    existwarning = self.exists()
                            if self.gdalexists==True:
                                errx= call([self.gdalprefix+"gdalwarp","-q","-s_srs",self.epsg, "-t_srs",self.epsg, "-wo","CUTLINE_ALL_TOUCHED=TRUE","-crop_to_cutline","-srcnodata",str(nodata),"-dstnodata",str(nodata),"-cutline",self.temp,layertocutFilePath,newfile],stderr=self.errorfile)
                                if errx==1:
                                    self.errmsg = "this error was created by gdalwarp at " + time.strftime('%X %x %Z')
                                    self.errorlog()
                            else:
                                k= processing.runalg('gdalogr:cliprasterbymasklayer', layertocut, self.temp,nodata, False, False,"-wo CUTLINE_ALL_TOUCHED=TRUE", folder +pref + str('%04d' %(i))+ ".tif")
                                del k
                            if self.dlg.addTiles.isChecked()== True:  
                                #add raster layer to canvas
                                fileInfo = QFileInfo(folder +pref + str('%04d' %(i))+".tif")
                                baseName = fileInfo.baseName()
                                layer = QgsRasterLayer(folder +pref + str('%04d' %(i))+".tif", baseName)
                                QgsMapLayerRegistry.instance().addMapLayer(layer)
                        
                        else: #run for vector layer
                            if layertocut.type()== QgsMapLayer.VectorLayer:
                                
                                newfile=folder+ pref +str('%04d' %(i))+".shp"
                                if os.path.isfile(newfile): #warn if file exists. But only warn once in big runs
                                    if existwarning == 0:
                                        existwarning = self.exists()
                                if self.gdalexists ==True:
                                    errx= call([self.gdalprefix+"ogr2ogr","-t_srs",self.epsg,"-s_srs",self.epsg,"-clipsrc" ,self.temp, newfile, layertocutFilePath], stderr=self.errorfile)
                                    if errx==1:
                                        self.errmsg = "this error was created by ogr2ogr at " + time.strftime('%X %x %Z')
                                        self.errorlog() 
                                else:
                                    k= processing.runalg('qgis:intersection', layertocut, self.gridtmp , folder+ pref +str('%04d' %(i))+".shp")
                                    del k
                                if self.dlg.addTiles.isChecked()== True:
                                    layer = QgsVectorLayer(folder+ pref +str('%04d' %(i))+".shp" , pref + str('%04d' %(i)), "ogr")
                                    QgsMapLayerRegistry.instance().addMapLayer(layer)
                    
                        self.cleanup()#clean up tempfile
                self.tileindex()
            else: #goon == false
                pass
        else: #option:cut by tile
            if not os.path.exists(self.outputfolder):
                os.makedirs(self.outputfolder) #make output base directory
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
                            
                            if self.dlg.subfolderRadio.isChecked():
                                folder= self.outputfolder + os.sep + str('%04d' %(i))+os.sep + str('%04d' %(j))+ os.sep 
                                if not os.path.exists(folder): #create folders
                                    os.makedirs(folder)
                                self.subpath=2
                            if self.dlg.nosubfolderRadio.isChecked():
                                folder = self.outputfolder+os.sep
                                self.subpath=0
                            nodata = layertocut.dataProvider().srcNoDataValue(1) #what about multiband rasters?
                            newfile = folder+pref+str('%04d' %(i))+"_"+str('%04d' %(j))+".tif"
                            if os.path.isfile(newfile): #warn if file exists. But only warn once in big runs
                                if existwarning == 0:
                                    existwarning = self.exists()
                            
                            #TODO experimental
                            if self.gdalexists ==True:
                                errx=call([self.gdalprefix+"gdalwarp","-q","-s_srs",self.epsg, "-t_srs",self.epsg, "-crop_to_cutline","-srcnodata",str(nodata),"-dstnodata",str(nodata),"-cutline",self.temp,layertocutFilePath,newfile], stderr=self.errorfile)
                                if errx==1:
                                    self.errmsg = "this error was created by gdalwarp at " + time.strftime('%X %x %Z')
                                    self.errorlog()
                            else:
                                k= processing.runalg('gdalogr:cliprasterbymasklayer', layertocut, self.temp , nodata, False, False, "",folder +pref + str('%04d' %(i))+"_"+str('%04d' %(j))+".tif")
                                del k
                            #add raster layer to canvas
                            if self.dlg.addTiles.isChecked()== True:
                                fileInfo = QFileInfo(folder +pref + str('%04d' %(i))+"_"+str('%04d' %(j))+".tif")
                                baseName = fileInfo.baseName()
                                layer = QgsRasterLayer(folder +pref + str('%04d' %(i))+"_"+str('%04d' %(j))+".tif", baseName)
                                QgsMapLayerRegistry.instance().addMapLayer(layer)
                                
                            #clean up
                            self.cleanup()
                    self.tileindex()
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
                                
                                if self.dlg.subfolderRadio.isChecked():
                                    folder= self.outputfolder + os.sep + str('%04d' %(i))+os.sep + str('%04d' %(j))+ os.sep
                                    if not os.path.exists(folder):
                                        os.makedirs(folder) #make folders
                                    self.subpath=2
                                if self.dlg.nosubfolderRadio.isChecked():
                                    folder= self.outputfolder+os.sep
                                    self.subpath=0
                                newfile = folder+ pref +str('%04d' %(i))+"_"+str('%04d' %(j))+".shp"
                                if os.path.isfile(newfile): #warn if file exists. But only warn once in big runs
                                    if existwarning == 0:
                                        existwarning = self.exists()
                                if self.gdalexists==True:
                                    errx=call([self.gdalprefix+"ogr2ogr","-t_srs",self.epsg,"-s_srs",self.epsg,"-clipsrc",self.temp, newfile, layertocutFilePath], stderr=self.errorfile)
                                    if errx==1:
                                        self.errmsg = "this error was created by ogr2ogr at " + time.strftime('%X %x %Z')
                                        self.errorlog()
                                else: 
                                    k= processing.runalg('qgis:intersection', layertocut, self.temp , folder+ pref +'%04d' %(str(i))+"_"+'%04d' %(str(j))+".shp")
                                    del k
                                #add to canvas
                                if self.dlg.addTiles.isChecked()== True:
                                    layer = QgsVectorLayer(folder+ pref +str('%04d' %(i))+"_"+str('%04d' %(j))+".shp" , pref +str('%04d' %(i))+"_"+str('%04d' %(j)), "ogr")
                                    QgsMapLayerRegistry.instance().addMapLayer(layer)
                                
                                #clean up
                                self.cleanup()
                        self.tileindex()
                    else:
                        pass
                        
        os.close(self.errorfile)
        
        
    def cleanup(self):
        QgsMapLayerRegistry.instance().removeMapLayers( [self.gridtmp.id()] )
        #close self.temp if it's open still
        if os.path.isfile(self.temp): #does not work on win7. runalg keeps them open
            QgsVectorFileWriter.deleteShapeFile(self.temp)
        cpg = self.temp[:-4]+ ".cpg"
        if os.path.isfile(cpg):
            os.remove(cpg)
            
    def temppolygon(self):
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
        #get a temp file name. Process should be less ugly
        tmpc, self.temp = tempfile.mkstemp(suffix='.shp', prefix='gridSplitter_tmpfile_')
        os.close(tmpc)
        os.remove(self.temp)
        writer = QgsVectorFileWriter.writeAsVectorFormat(self.gridtmp, self.temp,"utf-8",self.layertocutcrs,"ESRI Shapefile")
        #close tempfile
        del writer
        
        
    def warn(self):
        message= self.tr("you are about to make up to ") + str(self.amount) + self.tr(" tiles. Continue?")
        k = QMessageBox .question(None, "Grid Splitter", message, QMessageBox.Yes, QMessageBox.Abort)
        if k == QMessageBox.Yes:
            return True
        else:
            return False

    def reprojectTempFile(self):
        #reproject cutlayer into temporary memory layer
        message= self.tr("The Cutlayer doesn't match the projection of the layer to be cut. Should I try to reproject (temporary file)?")
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
            tmpc, tmp = tempfile.mkstemp(suffix='.shp', prefix='gridSplitter_reprojectedlayer_')
            os.close(tmpc)
            os.remove(tmp)
            c = self.cutlayer.dataProvider().dataSourceUri()
            cutlayername= c.split('|')[0]
            if self.gdalexists==True:
                errx=call([self.gdalprefix+"ogr2ogr","-t_srs",self.epsg,"-s_srs",srcsrs, tmp, cutlayername], stderr=self.errorfile)
                self.cutlayer = QgsVectorLayer(tmp,"reprojected Cutlayer","ogr")
                if errx==1:
                    self.errmsg = "this error was created by ogr2ogr at " + time.strftime('%X %x %Z')
                    self.errorlog()
            else:
                new= processing.runalg('qgis:reprojectlayer', self.cutlayer, self.epsg, None)
                self.cutlayer = QgsVectorLayer(new.get("OUTPUT"),"reprojected Cutlayer","ogr")
                del new
            QgsMapLayerRegistry.instance().addMapLayer(self.cutlayer)
        else: #don't reproject
            pass

    def exists(self):
      QMessageBox.information(None, self.tr("File exists"), self.tr("Some output files already exist. gridSplitter does not overwrite files, so results may be unexpected"))
      return 1
      
    def checkgdal(self):
    #check if GDALWARP is in the %Path. Assuming, ogr2ogr is there, too
        try:
            check_output(self.gdalprefix+'gdalwarp')
        except OSError:
            return False
        except CalledProcessError:
            return True

    def errorlog(self):
        if self.existerror == 0:
            QMessageBox.information(None, "Grid Splitter", self.tr("There was an error executing. See log for additional details"))
            self.existerror = 1
        errormessage= self.errmsg + os.linesep
        os.write(self.errorfile, errormessage)
    
    def tileindex(self):
        if self.dlg.tileindexCheck.isChecked():
            pref= self.dlg.prefixx.text()
            path=self.outputfolder
            index = self.dlg.inputRasterBox.currentIndex()
            layertocut = self.dlg.inputRasterBox.itemData(index)
            self.epsg=layertocut.crs().toProj4()
            if layertocut.type()== QgsMapLayer.RasterLayer:
                outputsuf= ".tif"
            if layertocut.type()== QgsMapLayer.VectorLayer:
                outputsuf= ".shp"
            if self.subpath==0:
                files= glob(self.outputfolder+os.sep+pref+"*"+outputsuf)
            else:
                if self.subpath==1:
                    files= glob(self.outputfolder+os.sep+"*"+os.sep+pref+"*"+outputsuf)
                else:
                    files= glob(self.outputfolder+os.sep+"*"+os.sep+"*"+os.sep+pref+"*"+outputsuf)
            
            if self.dlg.absolutePathCheck.isChecked():
                for f1 in files:
                    if layertocut.type()== QgsMapLayer.RasterLayer:
                        call([self.gdalprefix+'gdaltindex',"-write_absolute_path",'-t_srs',self.epsg,self.outputfolder+os.sep+pref+"tileindex.shp",f1], stderr=self.errorfile)
                    if layertocut.type()== QgsMapLayer.VectorLayer: #slightly different args
                        call([self.gdalprefix+'ogrtindex',"-write_absolute_path",self.outputfolder+os.sep+pref+"tileindex.shp",f1], stderr=self.errorfile)
            else:
                for f1 in files:
                    if layertocut.type()== QgsMapLayer.RasterLayer:
                        call([self.gdalprefix+'gdaltindex','-t_srs',self.epsg,self.outputfolder+os.sep+pref+"tileindex.shp",f1], stderr=self.errorfile)
                    if layertocut.type()== QgsMapLayer.VectorLayer: #slightly different args
                        call([self.gdalprefix+'ogrtindex',self.outputfolder+os.sep+pref+"tileindex.shp",f1], stderr=self.errorfile)
            layer = QgsVectorLayer(self.outputfolder+os.sep+pref+"tileindex.shp" , pref+"tileindex", "ogr")
            QgsMapLayerRegistry.instance().addMapLayer(layer)

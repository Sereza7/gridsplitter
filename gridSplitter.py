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
from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, QFileInfo, QVariant
from PyQt4.QtGui import QAction, QIcon, QMessageBox
# Initialize Qt resources from file resources.py
import resources_rc

from gridSplitter_dialog import gridSplitterDialog
from qgis.core import *
import os, os.path, processing, math, time
import tempfile
from subprocess import call, PIPE, Popen
from glob import glob

class gridSplitter:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(self.plugin_dir,'i18n',
                                   'gridSplitter_{}.qm'.format(locale))
        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)
        self.dlg = gridSplitterDialog()
        self.actions = []
        self.menu = self.tr(u'&gridSplitter')
        self.toolbar = self.iface.addToolBar(u'gridSplitter')
        self.toolbar.setObjectName(u'gridSplitter')

        #Config variables
        self.outputfolder = "" #required
        self.layertocut = "" #required
        #required: one of the three following set to True TODO ONLY one!
        self.cutlayeris = False
        self.numbertilesis = False
        self.tilesizeis = False

        self.cutlayer = "" #required for cutlayeris
        self.splicesX = 1 #required for numbertilesis
        self.splicesY = 1 #required for numbertilesis
        self.tilesizeX = 1.0 #required for tilesizeis
        self.tilesizeY = 1.0 #required for tilesizeis
        self.pref = "" #optional
        self.subfolderis = True #optional
        self.addtiles = True #optional
        self.tileindexis = False #optional
        self.reproj_temp = True #optional

    def tr(self, message):
        return QCoreApplication.translate('gridSplitter', message)

    def add_action(
        self, icon_path, text, callback, enabled_flag=True,
        add_to_menu=True, add_to_toolbar=True, status_tip=None,
        whats_this=None, parent=None):
      
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
            self.iface.removePluginMenu( self.tr(u'&gridSplitter'), action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar


    def sanitize(self, value):
        """removes invalid chars from inputs."""
        deletechars = '*:?"<>|'
        deletechars.push("'")
        for c in deletechars:
            value = value.replace(c,'')
        return value;


    def validate_inputs(self, gui = False):
        """ Validates the inputs and copies them from GUI to self. 
         If gui == True, output messages should be sent to a 
         QMessageBox, else to console (currently not implemented TODO
        """
        self.gui = gui
        errors = []
        try:
            self.outputfolder = self.dlg.OuptDir.text()
        except NameError:
            pass
        self.outputfolder = self.sanitize(self.outputfolder)
        if not os.access(self.outputfolder, os.W_OK) 
        or self.outputfolder = "":
            errors.push([self.tr("No valid cut layer!"), 
                         self.tr("Please specify a cut layer")])
        try:
            index = self.dlg.inputRasterBox.currentIndex()
            self.layertocut = self.dlg.inputRasterBox.itemData(index)
        except NameError:
            pass
        if self.layertocut == "":
            errors.push([self.tr("No layer to be cut"),
                         self.tr("Please specfy a layer to be cut")])
        try:
            self.cutlayeris = self.dlg.cutLayerRadio.isChecked()
        except NameError:
            pass
        if self.cutlayeris == true:
            try:
                index = self.dlg.cutLayerBox.currentIndex()
                self.cutlayer = self.dlg.cutLayerBox.itemData(index)
            except NameError:
                pass
            if self.cutlayer != "":
                errors.push([self.tr("No valid layer to cut"),
                         self.tr("Please specfy a layer to cut")])
        try:
            self.numbertilesis = self.dlg.numberTilesRadio.isChecked()
        except NameError:
            pass
        if numbertilesis == True:
            try:
                self.splicesX = int(self.dlg.splicesXSpinBox.text())
            except NameError:
                pass
            try:
                self.splicesY = int(self.dlg.splicesYSpinBox.text())
            except NameError:
                pass
        try:
            self.tilesizeis = self.dlg.tileSizeRadio.isChecked()
        except NameError:
            pass
        if self.tilesizeis == True:
            try:
                self.tilesizeX= float(self.dlg.tileSizeX.value())
            except NameError:
                pass
            #TODO : validate tilesizeX. typeof = float; > 0?
            try:
                self.tilesizeY= float(self.dlg.tileSizeY.value())
            except NameError:
                pass
            #TODO : validate tilesizeY. typeof = float; > 0?
        if self.chooseOptions() == False:
            errors.push([self.tr("Wrong amount of methods selected"),
                         self.tr("Please specify a single method to use.")])
        try:
            self.pref = self.dlg.prefixx.text()
        except NameError:
            pass
        self.pref = self.sanitize(self.pref)
        try:
            self.subfolderis = self.dlg.subfolderRadio.isChecked()
        except NameError:
            pass
        try:
            self.addtiles = self.dlg.addTiles.isChecked()
        except NameError:
            pass
        try:
            self.tileindexis = self.dlg.tileindexCheck.isChecked()
        except NameError:
            pass
        if len(errors) == 0:
            return True
        else:
            QMessageBox.information(None, "Grid Splitter",
                                    self.tr("There have been errors"))
            #for error in errors:
                #TODO: show error messages
            return False

    def run(self):
        """Starts the plugin with the GUI and gets variables """

        layers = QgsMapLayerRegistry.instance().mapLayers().values()
        for layer in layers:
            try:
                if layer.dataProvider().description().startswith('GDAL') 
                or layer.dataProvider().description().startswith('OGR'):
                    if layer.type() == QgsMapLayer.VectorLayer 
                    and layer.geometryType() == QGis.Polygon:
                        self.dlg.cutLayerBox.addItem( layer.name(), layer)
                        self.dlg.inputRasterBox.addItem(layer.name(), layer)
        except AttributeError:
            pass
        self.dlg.cutLayerBox.clear()
        self.dlg.inputRasterBox.clear()
        result = true
        self.dlg.show()
        while result == true:
            result = self.dlg.exec_()
            if result == true:
                if self.validate_inputs(True) == True:
                    success = self.operate()
                    if success == False:
                        return False#TODO inform that something is wrong
                    else:
                        return True
            else:
                return False


    def checkpreconditions(self):
        """checks preconditions (for now, if GDAL/OGR can be found"""
        if os.name == "nt":
            self.gdalprefix = QgsApplication.prefixPath()+ "/../../bin/"
        else:
            self.gdalprefix = ""
        try:
            call(self.gdalprefix+"gdalwarp")
        except OSError:
            self.gdalexists = False
        else:
            self.gdalexists = True
        return True
    
    def chooseOptions(self):
        count = 0
        if self.cutlayeris == True:
            count ++
        if self.numbertilesis == True:
            count ++
        if self.tilesizeis = True:
            count ++
        if count == 1:
            return True
        else:
            #TODO meaningful message
            return False

    def operate(self):
        """main method. Call this once all required variables are set"""

        try:
            self.preconditionsChecked
        except NameError:
            self.preconditionsChecked = self.checkpreconditions() 
        if self.validate_inputs() == False:
            return False
        self.errorfilename = tempfile.gettempdir() 
                            +os.sep 
                            + "gridsplitter-error.log"
        self.errorfile = os.open(
                                self.errorfilename,
                                os.O_APPEND|os.O_CREAT|os.O_RDWR)
        self.logfilename = tempfile.gettempdir() 
                           + os.sep 
                           + "gridsplitter-log.log"
        self.logfile = os.open(
                               self.logfilename,
                               os.O_APPEND|os.O_CREAT|os.O_RDWR)
        self.layertocutcrs = self.layertocut.crs()   
        ext = self.layertocut.extent()
        l = self.layertocut.dataProvider().dataSourceUri()
        layertocutFilePath= l.split('|')[0]
        existwarning = False
        self.existerror = False
        self.subpath = 0


        #option: cut by Cutlayer
        if self.cutlayeris:
            if not os.path.exists(self.outputfolder):
                os.makedirs(self.outputfolder)
            if self.gui == True:
                goon = self.warn(self.cutlayer.featureCount())
            else:
                goon = True
            if goon == False:
                return
            if self.layertocutcrs != self.cutlayer.crs():
                self.reprojectTempFile()
            else:
                self.epsg = self.layertocutcrs.toProj4()
            iter = self.cutlayer.getFeatures()
            for feature in iter:
                if feature.geometry().intersects(ext):
                    #TODO: Does an index speed up things?
                    self.poly = feature
                    self.temppolygon()
                    if self.subfolderis == True:
                        folder = self.outputfolder
                                 + os.sep
                                 + str('%04d' %(feature.id()))
                                 + os.sep
                        if not os.path.exists(folder):
                            os.makedirs(folder)
                            self.subpath=1
                    else:
                        folder = self.outputfolder+os.sep
                        self.subpath=0
                    #run rasterlayer
                    if self.layertocut.type() == QgsMapLayer.RasterLayer:
                        nodata = self.layertocut.dataProvider().srcNoDataValue(1)
                        #TODO what about NoData on multiband rasters?
                        self.epsg=self.layertocutcrs.toProj4()
                        newfile = folder 
                                  + self.pref 
                                  + str('%04d' %(feature.id()))
                                  + ".tif"
                                  #TODO: other output options
                        if os.path.isfile(newfile):
                            if existwarning == False:
                                existwarning = self.exists()
                        if self.gdalexists == True:
                            self.Popenargs=[self.gdalprefix + "gdalwarp",
                                            "-q",
                                            "-s_srs",self.epsg, 
                                            "-t_srs",self.epsg, 
                                            "-wo","CUTLINE_ALL_TOUCHED=TRUE",
                                            "-crop_to_cutline",
                                            "-srcnodata", str(nodata),
                                            "-dstnodata", str(nodata),
                                            "-cutline", 
                                            self.temp,
                                            layertocutFilePath,
                                            newfile]
                            errx= self.runPopen()
                            if errx==1:
                                self.errmsg = "this error was created by "
                                              + " gdalwarp at " 
                                              + time.strftime('%X %x %Z')
                                self.errorlog()
                        else: #gdalexists == False
                            k = processing.runalg('gdalogr:cliprasterbymasklayer',
                                                  self.layertocut,
                                                  self.temp,
                                                  nodata,
                                                  False,
                                                  False,
                                                  "-wo CUTLINE_ALL_TOUCHED=TRUE",
                                                  newfile)
                            del k
                        if self.addtiles == True:
                            fileInfo = QFileInfo(newfile)
                            baseName = fileInfo.baseName()
                            layer = QgsRasterLayer(newfile, baseName)
                            QgsMapLayerRegistry.instance().addMapLayer(layer)
                    else: #run for vector layer
                        if self.layertocut.type() == QgsMapLayer.VectorLayer:
                            newfile = folder+ self.pref 
                                      + str('%04d' %(feature.id()))+".shp"
                            if os.path.isfile(newfile):
                                if existwarning == False:
                                    existwarning = self.exists()
                                if self.gdalexists == True:
                                    self.Popenargs=[self.gdalprefix 
                                                    + "ogr2ogr",
                                                    "-t_srs", self.epsg,
                                                    "-s_srs", self.epsg,
                                                    "-clipsrc" , 
                                                    self.temp,
                                                    newfile,
                                                    layertocutFilePath]
                                    errx = self.runPopen()
                                    if errx == 1:
                                        self.errmsg = "this error was created "
                                                      + "by ogr2ogr at " 
                                                      + time.strftime('%X %x %Z')
                                        self.errorlog()
                                else: #gdalexists == False
                                    k = processing.runalg('qgis:intersection',
                                                          self.layertocut,
                                                          self.gridtmp,
                                                          folder + self.pref
                                                          + str('%04d' %(feature.id()))
                                                          + ".shp")
                                    del k
                                if self.addtiles == True:
                                    layer = QgsVectorLayer(newfile, 
                                                           self.pref
                                                           + str('%04d' %(feature.id())),
                                                           "ogr")
                                    QgsMapLayerRegistry.instance().addMapLayer(layer)
                    self.cleanup()
            self.tileindex()

        #option: cut by Tile
        else:
            if not os.path.exists(self.outputfolder):
                os.makedirs(self.outputfolder)
            self.epsg=self.layertocutcrs.toProj4()
            xmax = float(self.layertocut.extent().xMaximum())
            xmin = float(self.layertocut.extent().xMinimum())
            ymax = float(self.layertocut.extent().yMaximum())
            ymin = float(self.layertocut.extent().yMinimum())

            #option cut by tile, raster layer
            if self.layertocut.type() == QgsMapLayer.RasterLayer:
                 # Get the extents and calculate so it doesn't cut pixels.
                 # Make the tiles up to one pixel larger if they cut
                rwidth = float(self.layertocut.width())
                rheight = float(self.layertocut.height())
                #WMS layer fails here: ZeroDivisionError (disabled WMS layer)
                xres = (xmax - xmin) / rwidth
                yres = (ymax - ymin) / rheight
                
                #if tile number is given
                if self.numbertilesis == True:
                    ixx= float(rwidth) / self.splicesX
                    iyy= float(rheight)/ self.splicesY
                    xsplice = math.ceil(ixx) * xres
                    ysplice = math.ceil(iyy) * yres

                #if tile size is given
                if self.tilesizeis == True:
                    #snap tilesize up to resolution
                    xsplice = math.ceil(float(self.tilesizeX)/xres) * xres
                    ysplice = math.ceil(float(self.tilesizeY)/yres) * yres
                    self.splicesX = int(math.ceil((xmax -xmin)/ float(xsplice)))
                    self.splicesY = int(math.ceil((ymax -ymin)/ float(ysplice)))
                goon = self.warn(splicesX * splicesY)    
                if goon == False:
                    return False
                for i in range(self.splicesX):
                    for j in range(self.splicesY):

                        #make a temporary Polygon
                        xsplmin= xmin + i*xsplice
                        xsplmax= xmin + (i+1)*xsplice
                        ysplmin= ymin + j*ysplice
                        ysplmax = ymin + (j+1)*ysplice
                        pol= "POLYGON ((" + str(xsplmin) + " " + str(ysplmin)
                        + ", " + str(xsplmax) + " " + str(ysplmin) + ", "
                        + str(xsplmax) + " " + str(ysplmax) + ", "
                        + str(xsplmin) + " " + str(ysplmax) + ", " 
                        + str(xsplmin) + " " + str(ysplmin) + "))"
                        self.poly = QgsFeature()
                        self.poly.setGeometry(QgsGeometry.fromWkt(pol))
                        self.temppolygon()
                        if self.subfolderis == True:
                            folder = self.outputfolder + os.sep 
                                     + str('%04d' %(i)) + os.sep
                                     + str('%04d' %(j)) + os.sep 
                            if not os.path.exists(folder):
                                os.makedirs(folder)
                            self.subpath=2
                        else:
                            folder = self.outputfolder + os.sep
                            self.subpath=0
                        nodata = self.layertocut.dataProvider().srcNoDataValue(1)
                        newfile = folder + self.pref + str('%04d' %(i)) 
                                  + "_" + str('%04d' %(j)) + ".tif"
                        if os.path.isfile(newfile):
                            if existwarning == False:
                                existwarning = self.exists()
                        if self.gdalexists == True:
                            self.Popenargs=[self.gdalprefix
                                            + "gdalwarp",
                                            "-q",
                                            "-s_srs", self.epsg,
                                            "-t_srs", self.epsg,
                                            "-crop_to_cutline",
                                            "-srcnodata", str(nodata),
                                            "-dstnodata", str(nodata),
                                            "-cutline", self.temp,
                                            layertocutFilePath, newfile]
                            errx=self.runPopen()
                            if errx==1:
                                self.errmsg = "this error was created by"
                                              + "gdalwarp at " 
                                              + time.strftime('%X %x %Z')
                                self.errorlog()
                        else:
                            k= processing.runalg('gdalogr:cliprasterbymasklayer',
                                                 self.layertocut,
                                                 self.temp,
                                                 nodata,
                                                 False,
                                                 False,
                                                 "",
                                                 newfile)
                            del k
                        if self.addtiles == True:
                            fileInfo = QFileInfo(newfile)
                            baseName = fileInfo.baseName()
                            layer = QgsRasterLayer(newfile,baseName)
                            QgsMapLayerRegistry.instance().addMapLayer(layer)
                self.cleanup()
                self.tileindex()
            #option cut by tile, vector layer
            else:
                if layertocut.type() == QgsMapLayer.VectorLayer:
                    if self.numbertilesis == True:
                        xsplice = (xmax - xmin) / self.splicesX
                        ysplice = (ymax - ymin) / self.splicesY
                    else:
                        if self.tilesizeis == True:
                            xsplice = tilesizeX
                            ysplice = tilesizeY
                            self.splicesX = int(math.ceil((xmax-xmin)
                                                          /float(tilesizeX)))
                            self.splicesY = int(math.ceil((ymax-ymin)
                                                          /float(tilesizeY)))
                    goon = self.warn(self.splicesX*self.splicesY)
                    if goon == False:
                        return False
                    for i in range(self.splicesX):
                        for j in range(self.splicesY):
                            xsplmin= xmin + i*xsplice
                            xsplmax= xmin + (i+1)*xsplice
                            ysplmin= ymin + j*ysplice
                            ysplmax = ymin + (j+1)*ysplice
                            pol= "POLYGON ((" + str(xsplmin) + " " 
                            + str(ysplmin) + ", " + str(xsplmax) + " "
                            + str(ysplmin) + ", " + str(xsplmax) + " "
                            + str(ysplmax) + ", " + str(xsplmin) + " "
                            + str(ysplmax) + ", " + str(xsplmin) + " "
                            + str(ysplmin) + "))"
                            self.poly = QgsFeature()
                            self.poly.setGeometry(QgsGeometry.fromWkt(pol))
                            self.temppolygon()
                            if self.subfolderis == True:
                                folder = self.outputfolder + os.sep 
                                         + str('%04d' %(i)) + os.sep
                                         + str('%04d' %(j)) + os.sep
                                if not os.path.exists(folder):
                                    os.makedirs(folder)
                                self.subpath = 2
                            else:
                                folder = self.outputfolder + os.sep
                                self.subpath = 0
                            newfile = folder + self.pref + str('%04d' %(i))
                                      + "_" + str('%04d' %(j)) + ".shp"
                            if os.path.isfile(newfile):
                                if existwarning == False:
                                    existwarning = self.exists()
                            if self.gdalexists == True:
                                self.Popenargs = [self.gdalprefix + "ogr2ogr",
                                                 "-t_srs", self.epsg,
                                                 "-s_srs", self.epsg,
                                                 "-clipsrc", self.temp,
                                                 newfile, layertocutFilePath]
                                errx = self.runPopen()
                                if errx==1:
                                    self.errmsg = "this error was created by"
                                                  +"ogr2ogr at " 
                                                  + time.strftime('%X %x %Z')
                                    self.errorlog()
                            else:
                                k= processing.runalg('qgis:intersection',
                                                     self.layertocut,
                                                     self.temp, 
                                                     folder + newfile)
                                del k
                            if self.addtiles == True:
                                layer = QgsVectorLayer(newfile, 
                                                       self.pref 
                                                       + str('%04d' %(i))
                                                       + "_" 
                                                       + str('%04d' %(j)),
                                                       "ogr")
                                QgsMapLayerRegistry.instance().addMapLayer(layer)
                    self.cleanup()
                    self.tileindex()
        os.close(self.errorfile)
        os.close(self.logfile)


    def cleanup(self):
        """Tries to remove temporary files and map layers
        Only partially works, as on Windows there is FileLocks
        """
        QgsMapLayerRegistry.instance().removeMapLayers([self.gridtmp.id()])
        if os.path.isfile(self.temp):
                QgsVectorFileWriter.deleteShapeFile(self.temp)
                #TODO: error handling on Windows?
        #deleteShapeFile does not delete "cpg" files created
        cpg = self.temp[:-4] + ".cpg"
        if os.path.isfile(cpg):
            os.remove(cpg)


    def temppolygon(self):
        """Creates a temporary polygon file. GDAL/OGR does not like
        pure memory layers"""
        self.epsg = self.layertocutcrs.toWkt()
        tmpf= "Polygon?crs=" + self.epsg
        self.gridtmp = QgsVectorLayer(tmpf, "gridtile", "memory")
        QgsMapLayerRegistry.instance().addMapLayer(self.gridtmp)
        self.gridtmp.startEditing()
        fet = QgsFeature()
        fet.setGeometry(self.poly.geometry())
        pr = self.gridtmp.dataProvider()
        pr.addFeatures([fet])
        self.gridtmp.commitChanges()

        tmpc, self.temp = tempfile.mkstemp(suffix='.shp', prefix='gridSplitter_tmpfile_')
        os.close(tmpc)
        os.remove(self.temp)
        writer = QgsVectorFileWriter.writeAsVectorFormat(self.gridtmp,
                                                         self.temp,
                                                         "utf-8",
                                                         self.layertocutcrs,
                                                         "ESRI Shapefile")
        del writer


    def warn(self, amount):
        """Print a warning before starting many operations"""
        message= self.tr("you are about to make up to ")
                         + str(amount) 
                         + self.tr(" tiles. Continue?")
        k = QMessageBox .question(None,
                                  "Grid Splitter",
                                  message,
                                  QMessageBox.Yes,
                                  QMessageBox.Abort)
        if k == QMessageBox.Yes:
            return True
        else:
            return False


    def reprojectTempFile(self):
        """reproject 'cutlayer' into temporary memory layer"""
        if self.gui == True:
            message= self.tr("The Cutlayer doesn't match the projection of "
                             +"the layer to be cut. Should I try to reproject"
                             +"(temporary file)?")
            k = QMessageBox.question(None, "Grid Splitter",
                                     message,
                                     QMessageBox.Yes,
                                     QMessageBox.No)
            if k == QMessageBox.Yes:
                self.reproj_temp == True
            else:
                self.reproj_temp == False
        if self.reproj_temp == True:
            self.epsg = self.layertocutcrs.toProj4()
            cutlayersrs = self.cutlayer.crs()
            srcsrs = cutlayersrs.toProj4()
            tmpc, tmp = tempfile.mkstemp(suffix='.shp', prefix='gridSplitter_reprojectedlayer_')
            os.close(tmpc)
            os.remove(tmp)
            c = self.cutlayer.dataProvider().dataSourceUri()
            cutlayername= c.split('|')[0]
            if self.gdalexists == True:
                self.Popenargs = [self.gdalprefix
                                  + "ogr2ogr",
                                  "-t_srs", self.epsg,
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
                new = processing.runalg('qgis:reprojectlayer',
                                        self.cutlayer,
                                        self.epsg,
                                        None)
                self.cutlayer = QgsVectorLayer(new.get("OUTPUT"),
                                               "reprojected Cutlayer",
                                               "ogr")
                del new
            QgsMapLayerRegistry.instance().addMapLayer(self.cutlayer)

    def exists(self):
      if self.gui == True:
          QMessageBox.information(None, 
                                  self.tr("File exists"), 
                                  self.tr("Some output files already exist.",
                                      "gridSplitter does not overwrite files,",
                                      "so results may be unexpected"))
      return True


    def errorlog(self):
        if self.existerror == False:
            if self.gui == True:
                QMessageBox.information(None, 
                                        "Grid Splitter",
                                        self.tr("There was an error executing. "
                                                +"See log for additional details"))
            self.existerror = True
        errormessage = self.errmsg + os.linesep
        os.write(self.errorfile, errormessage)


    def tileindex(self):
        """Creates a index shapefile with gdaltindex showing the names and
        position of individual tiles. Requires GDAL/OGR"""
        if self.tileindexis == True and self.gdalexists == True:
            self.epsg = self.layertocut.crs().toProj4()
            if self.layertocut.type() == QgsMapLayer.RasterLayer:
                outputsuf = ".tif"
            if self.layertocut.type() == QgsMapLayer.VectorLayer:
                outputsuf = ".shp"
            if self.subpath == 0:
                files= glob(self.outputfolder + os.sep + self.pref + "*" 
                            + outputsuf)
            else:
                if self.subpath == 1:
                    files= glob(self.outputfolder + os.sep + "*" + os.sep
                                + self.pref + "*" + outputsuf)
                else:
                    files= glob(self.outputfolder + os.sep + "*" + os.sep
                                + "*" + os.sep + self.pref + "*" + outputsuf)
            for file in files:
                if self.layertocut.type() == QgsMapLayer.RasterLayer:
                    self.Popenargs=[self.gdalprefix 
                                    + 'gdaltindex',
                                    '-t_srs', self.epsg,
                                    self.outputfolder 
                                    + os.sep + self.pref
                                    + "tileindex.shp",
                                    file]
                    self.runPopen()
                    if self.layertocut.type() == QgsMapLayer.VectorLayer:
                        self.Popenargs=[self.gdalprefix
                                        + 'ogrtindex',
                                        self.outputfolder 
                                        + os.sep + self.pref
                                        + "tileindex.shp",
                                        file]
                        self.runPopen()
            layer = QgsVectorLayer(self.outputfolder + os.sep 
                                   + self.pref + "tileindex.shp",
                                   self.pref + "tileindex",
                                   "ogr")
            QgsMapLayerRegistry.instance().addMapLayer(layer)
            #fill the layer with information about path/row
            layer.dataProvider().addAttributes([QgsField("row",
                                                         QVariant.String,
                                                         "",
                                                         10),
                                                QgsField("col",
                                                         QVariant.String,
                                                         "",
                                                         10)])
            layer.updateFields()
            layer.startEditing()
            for feature in layer.getFeatures():
                withoutextension = feature['location'].split('.')[-2]
                withoutpath = withoutextension.split(os.sep)[-1]
                withoutprefix = withoutextension.split(self.pref)[-1]
                feature['col'] = withoutprefix.split('_')[0]
                #we don't always have a row!
                try:
                    feature['row'] = withoutprefix.split('_')[1]
                except IndexError:
                    pass
                layer.updateFeature(feature)
            d = layer.commitChanges()


ś    def runPopen(self):
        """Special treatment of windows, to avoid consoles popping up on 
        every call"""
        if os.name == "nt":
            p = Popen(self.Popenargs,
                    stdin=PIPE,
                    stdout=self.logfile,
                    stderr=self.errorfile,
                    creationflags=0x08000000)
            e = p.wait()
        else:
            p = Popen(self.Popenargs,
                      stdin=PIPE,
                      stdout=self.logfile,
                      stderr=self.errorfile)
            e = p.wait()
        return e

# -*- coding: utf-8 -*-
"""
/***************************************************************************
 gridSplitter
 Example code for plugin usage outside the GUI, but called from python
 console.
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
import qgis.core
import qgis.utils
import imp

iface = qgis.utils.iface
module = imp.load_source('gridSplitter',
                         '/path/to/python/plugins/gridSplitter/')

mySplitter = module.gridSplitter.gridSplitter(iface)

# module.run() # runs with GUI

module.outputfolder = '/path/to/output/'
module.layertocut = QgsVectorLayer('/path/to/file.shp', 'input', 'ogr')

module.cutlayeris = True
module.cutlayer = QgsVectorLayer('/path/to/otherfile.shp',
                                 'scissor layer', 'ogr')

module.pref = 'cut_'
module.tileindexis = True

module.operate()  # runs without GUI

# gridsplitter
A QGIS plugin that creates tiles from an input layer
=================

The gridSplitter is written to cleanly cut input features. It is a wrapper for gdalogr:cliprasterbymasklayer
and qgis:intersection or, if found, gdal/ogr. It takes the extent of the input data, divides it by a number of pieces and saves 
those pieces to an output directory and subdirectories. 

It aims to be functional in any coordinate reference 
system and with any number (up to 9999*9999) of pieces (or tiles). It saves its outputs in .TIF and .shp, respectively.

The initial plugin used the "plugin builder" from Qgis; this is my first plugin, so redundant and ugly code is to be expected.

Dependencies
=================
It depends on QGIS and GDAL, although it runs even when those are not found.

Running the plugin
=================
The plugin needs a layer to be loaded in QGIS to process it. 


Changelog
=================
v. 0.3.5 bugfix

    bug github #1: TypeError when no GDAL is found
   
v.0.3.4 minor additions, bugfixes
   
    bug 13935 openlayers blocking start of plugin
    
    bug 13921: UI improvement
    
    bug 13922: ansolute path doesn't work, removing option for now
    
    feature request 13923: adding col and row to the tileindex shapefile
    

v.0.3.3 minor changes

    translation to german

    improved finding of GDAL in WIN

    added error log into temp directory
    
    added tileindex creation

v.0.3.2 minor changes and bug fix

    added gdalwarp/ogr2ogr directly; (better use of nodata, more raster types supported)
    
    removed everything to do with qgis.gui, as it didn't work on W7
    
    worked around file locking of tempfiles
    
	
    moved "tempfile" to automatic handling
	
    added reprojection of cutlayer if desired
    
    added warning for operations pending
    
    added handling of user-defined CRS
    
    cut raster by cutlayer: no more gaps

v 0.3.1 bugfix for 0.3.0

    typo in "raster by tile size" fixed

    typos which affected polygon cutting and naming

    general rewrite for readability

v 0.3: new features

    Added option to cut by map units, and to cut by cutlayer features

v 0.2: new feature

    Map tiles can be added to canvas after running

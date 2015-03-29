# gridsplitter
A QGIS plugin that creates tiles from an input layer
=================

The gridSplitter is written to cleanly cut input features. It is a wrapper for gdalogr:cliprasterbymasklayer
and qgis:intersection. It takes the extent of the input data, divides it by a number of pieces and saves 
those pieces to an output directory and subdirectories. 

It aims to be functional in any coordinate reference 
system and with any number of pieces (or tiles). It saves its outputs in .TIF and .shp, respectively.

The initial plugin used the "plugin builder" from Qgis; this is my first plugin, so redundant and ugly code is to be expected.

Dependencies
=================
It depends on QGIS and GDAL.

Running the plugin
=================
The plugin needs a layer to be loaded in QGIS to process it. 


Changelog
=================
v.0.3.2  added warning for operations pending
	
	added handling of user-defined CRS

v 0.3.1 typo in "raster by tile size" fixed

	typos which affected polygon cutting and naming

	general rewrite for readability

v 0.3: Added option to cut by map units, and to cut by cutlayer features

v 0.2: Map tiles can be added to canvas after running

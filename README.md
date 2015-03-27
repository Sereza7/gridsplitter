# gridsplitter
A QGIS plugin that creates tiles from an input layer
=================

The gridSplicer is written to cleanly cut input features. It is a wrapper for gdalogr/cliprasterbymasklayer
and qgis:intersection. It takes the extent of the input data, divides it by a number of pieces and saves 
those pieces to an output directory and subdirectories. It aims to be functional in any coordinate reference 
system and with any number of pieces (or tiles). It saves its outputs in .TIF and .shp, respectively.

Running the plugin
=================
The plugin needs a layer to be loaded in QGIS to process it. The output layers won't be added to the canvas, 
as this is not useful when making lots of pieces.


Required Parameters
...................
:Input Layer: The layer to be processed. Can be a raster or a vector layer.

:Number of tiles X: Numbers of pieces/tiles in X direction

:Number of tiles Y: Numbers of pieces/tiles in X direction

:Output Dir: Base Directory where the output will be stored. Subdirectories will be created which indicate
the tiles.

:temporary file: Since the algorithm can't process an in-memory layer, a temporary shapefile will be created 
and deleted at the end, used for iterations.



Optional Parameters
...................

:prefix: The prefix output files will have.

Changelog
=================
v 0.2:
Map tiles can be added to canvas after running

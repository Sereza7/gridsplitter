
Welcome to gridSplitter's documentation!
============================================

Concept
=================

The gridSplitter is written to cleanly cut input features. It is a wrapper for gdalogr/cliprasterbymasklayer
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

:Output Dir: Base Directory where the output will be stored. Subdirectories will be created which indicate
the tiles.

:temporary file: Since the algorithm can't process an in-memory layer, a temporary shapefile will be created 
and deleted at the end, used for iterations.

:Method: One of the methods has to be selected (See below).


Optional Parameters
...................

:prefix: The prefix output files will have.

:add to map layer: The layers created will be loaded into QGIS.

Methods
================
gridSplitter offers three methods for splitting. Cutting by tile number, cutting by tile size, and cutting by layer feature,

Cutting by tile number:

Select the number of tiles in X axis and Y axis, and it will calculate how big a tile needs to be.

Cutting by tile size:

Enter size in map units for both axis and it will calculate the number of tiles needed.

Cutting by Layer:

A tile for every feature will be created.

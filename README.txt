
Welcome to gridSplitter's documentation!
============================================

Concept
=================

The gridSplitter is written to cleanly cut input features. It is a wrapper for gdalogr/cliprasterbymasklayer
and qgis:intersection. 
It has several options:

The first option, cut by tile number (v.0.1), takes the extent of the input data, divides it by a number of 
pieces and saves those pieces to an output directory and subdirectories. 
It checks for gaps and makes the tiles a tiny bit (up to one pixel inpput resolution) bigger if needed.

The second option, (v.0.3) cut by tile size, takes as user input the tile size in input map units and determines the 
number of tiles needed, saving those into subdirectories.
It checks for gaps and makes the tiles a tiny bit (up to one pixel input resolution) bigger 
So, if size given is a multiplier of "5m" and a pixel resolution of 5.1 m is given, the tile will be a multiplier of 5.1m.

The third option (v.0.3) takes a cut layer and cuts a piece for ecery feature in the cut layer. This option does not 
check for overlaps.

It aims to be functional in any coordinate reference system. It also takes User-defined CRS (v.0.3.2).

It saves its outputs in .TIF and .shp, respectively.

Running the plugin
=================
The plugin needs a layer to be loaded in QGIS to process it. It then loops until all input parameters are set, 
and then warns the user of the amount of cutting upcoming (v.0.3,2). 

If desired, the newly created tiles will be added to QGIS, if not, they'll just be stored on hard disk.

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

A tile for every feature will be created. If the CutLayer is in a non-matching projection, a reprojection will be attempted. 
(original file won't be modified)

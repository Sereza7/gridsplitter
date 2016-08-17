
Welcome to gridSplitter's documentation!
============================================

Concept
=================

The gridSplitter is written to cleanly cut input features. It is a wrapper for
either gdalogr/cliprasterbymasklayer and qgis:intersection or, if found, 
gdalwarp/ogr2ogr.

It has several options:

The first option, cut by tile number, takes the extent of the input 
data, divides it by a number of pieces and saves those pieces to an output 
directory and subdirectories. It checks for gaps and makes the tiles a tiny 
bit (up to one pixel inpput resolution) bigger if needed.

The second option, cut by tile size, takes as user input the tile 
size in input map units and determines the number of tiles needed, saving
those into subdirectories. It checks for gaps and makes the tiles a tiny 
bit (up to one pixel input resolution) bigger So, if size given is a 
multiplier of "5m" and a pixel resolution of 5.1 m is given, the tile will 
be a multiplier of 5.1m.

The third option takes a cut layer and cuts a piece for ecery
feature in the cut layer. This option does not check for overlaps.

It aims to be functional in any coordinate reference system. It also takes 
User-defined CRS.

It saves its outputs in .TIF and .shp, respectively.

Running the plugin
=================
The plugin needs a layer to be loaded in QGIS to process it. It then checks
if all input parameters are set, and then warns the user of the amount of 
cutting upcoming. 

If desired, the newly created tiles will be added to QGIS, if not, they will
just be stored on hard disk.

**New: Running the plugin as batch job**
=================
After a cleanup, the cutting now can be invoked from anywhere inside QGIS
(e.g. a python script or another plugin). You need to import the module
and provide the following config variables:

module.outputfolder # string required: The base folder where the data is to be stored
module.layertocut # maplayer required: A loaded layer to be cut.

#one of the following set to True: 
module.cutlayeris # bool cut the layertocut by another layer 
module.numbertilesis # bool cut the layertocut by amount of tiles
module.tilesizeis # bool cut the layertocut by size

module.cutlayer # maplayer required for cutlayeris
module.splicesX # int required for numbertilesis, default: 1
module.splicesY # int required for numbertilesis, default: 1
module.tilesizeX # float required for tilesizeis, default: 1.0
module.tilesizeY # float required for tilesizeis, default: 1.0
module.pref # string optional prefix for the naming of output files
module.subfolderis # bool optional. If true, there will be subfolders
module.addtiles # bool optional. If true, all output is opened in QGIS
module.tileindexis # bool optional. If true, a tile index will be created
module.reproj_temp # bool optional If true, files will be reprojected as needed

Required Parameters
...................
:Input Layer: The layer to be processed. Can be a raster or a vector layer.

:Output Dir: Base Directory where the output will be stored. Subdirectories will be created which indicate
the tiles.

:Method: One of the methods has to be selected (See below).


Optional Parameters
...................
:tile index creation: A tile index shapefile will be created in the Output base folder, storing the bounding boxes of all output files. 

 :write absolute path: The tile index created will be filled with absoulte file paths instead of relative ones.

:prefix: The prefix output files will have.

:add to map layer: The layers created will be loaded into QGIS.

:create tileindex: Uses gdaltindex for creating a shapefile that contains spatial information about every file created. 

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


Why using gdal/ogr binaries directly?
==================
They close the file after using properly, so  temp files can be deleted
It supports more input data (e.g. georeferenced jpg)
possibility to change things later on (cblend, nodata value, ...)
using one less layer of things should speed it up a bit.

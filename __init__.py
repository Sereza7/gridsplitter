# -*- coding: utf-8 -*-
"""
/***************************************************************************
 gridSplitter
                                 A QGIS plugin
 A plugin that cuts a layer into pieces(tiles)
                             -------------------
        begin                : 2015-03-26
        copyright            : (C) 2015 by Maximilian Krambach
        email                : maximilian.krambach@gmx.de
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load gridSplitter class from file gridSplitter.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .gridSplitter import gridSplitter
    return gridSplitter(iface)

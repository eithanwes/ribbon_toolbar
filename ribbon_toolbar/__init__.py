# -*- coding: utf-8 -*-
"""
Ribbon Toolbar - A Microsoft Office-like ribbon interface for QGIS.
"""


def classFactory(iface):
    from .ribbon_plugin import RibbonToolbarPlugin

    return RibbonToolbarPlugin(iface)

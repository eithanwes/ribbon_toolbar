# -*- coding: utf-8 -*-
"""
Main plugin class for Ribbon Toolbar.
Handles plugin lifecycle and toggling between ribbon and classic UI.
"""

from pathlib import Path

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QToolBar


class RibbonToolbarPlugin:
    """QGIS Plugin: Replaces menus/toolbars with a ribbon interface."""

    RIBBON_OBJECT_NAME = "RibbonToolbarMain"

    def __init__(self, iface):
        self.iface = iface
        self.main_window = iface.mainWindow()
        self.ribbon_active = False
        self.ribbon_toolbar = None
        self.ribbon_widget = None
        self.toggle_action = None
        # Store original visibility states for toolbars
        self._original_toolbar_visibility = {}
        self._original_menubar_visible = True
        self.plugin_dir = Path(__file__).parent

    def initGui(self):
        """Called when plugin is loaded."""
        icon_path = self.plugin_dir / "icon.png"
        icon = QIcon(str(icon_path)) if icon_path.exists() else QIcon()

        # Toggle action
        self.toggle_action = QAction(icon, "Toggle Ribbon Toolbar", self.main_window)
        self.toggle_action.setCheckable(True)
        self.toggle_action.setChecked(False)
        self.toggle_action.triggered.connect(self._on_toggle)
        self.iface.addToolBarIcon(self.toggle_action)
        self.iface.addPluginToMenu("&Ribbon Toolbar", self.toggle_action)

    def unload(self):
        """Called when plugin is unloaded."""
        if self.ribbon_active:
            self._deactivate_ribbon()
        self.iface.removePluginMenu("&Ribbon Toolbar", self.toggle_action)
        self.iface.removeToolBarIcon(self.toggle_action)

    def _on_toggle(self, checked):
        if checked:
            self._activate_ribbon()
        else:
            self._deactivate_ribbon()

    def _activate_ribbon(self):
        """Hide menus/toolbars and show the ribbon."""
        if self.ribbon_active:
            return

        # Save current state
        self._original_menubar_visible = self.main_window.menuBar().isVisible()
        self._original_toolbar_visibility = {}
        for tb in self.main_window.findChildren(QToolBar):
            if tb.objectName() != self.RIBBON_OBJECT_NAME:
                self._original_toolbar_visibility[tb.objectName()] = tb.isVisible()

        # Build the ribbon
        from .ribbon_widget import RibbonWidget

        self.ribbon_widget = RibbonWidget(self.iface, self.main_window)

        # Create the hosting toolbar
        self.ribbon_toolbar = QToolBar("Ribbon", self.main_window)
        self.ribbon_toolbar.setObjectName(self.RIBBON_OBJECT_NAME)
        self.ribbon_toolbar.setMovable(False)
        self.ribbon_toolbar.setFloatable(False)
        self.ribbon_toolbar.setContextMenuPolicy(Qt.PreventContextMenu)

        self.ribbon_widget.build_ribbon()
        self.ribbon_toolbar.addWidget(self.ribbon_widget)
        self.main_window.addToolBar(Qt.TopToolBarArea, self.ribbon_toolbar)

        # Hide all existing toolbars and menubar
        for tb in self.main_window.findChildren(QToolBar):
            if tb.objectName() != self.RIBBON_OBJECT_NAME:
                tb.setVisible(False)
        self.main_window.menuBar().setVisible(False)

        self.ribbon_active = True

    def _deactivate_ribbon(self):
        """Restore menus/toolbars and remove the ribbon."""
        if not self.ribbon_active:
            return

        # Remove ribbon
        if self.ribbon_toolbar:
            self.main_window.removeToolBar(self.ribbon_toolbar)
            self.ribbon_toolbar.deleteLater()
            self.ribbon_toolbar = None
            self.ribbon_widget = None

        # Restore menubar
        self.main_window.menuBar().setVisible(self._original_menubar_visible)

        # Restore toolbars
        for tb in self.main_window.findChildren(QToolBar):
            name = tb.objectName()
            if name in self._original_toolbar_visibility:
                tb.setVisible(self._original_toolbar_visibility[name])

        self.ribbon_active = False
        self.toggle_action.setChecked(False)

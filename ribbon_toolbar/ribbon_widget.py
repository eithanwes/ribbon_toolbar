# -*- coding: utf-8 -*-
"""
Ribbon widget — a QTabWidget styled like a Microsoft Office ribbon.
Each tab corresponds to a QGIS menu. Within each tab, actions are
organized into labeled groups with large/small icon buttons.
"""

import re

from qgis.PyQt import sip
from qgis.PyQt.QtCore import QSize, Qt
from qgis.PyQt.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMenu,
    QScrollArea,
    QSizePolicy,
    QTabWidget,
    QToolBar,
    QToolButton,
    QVBoxLayout,
    QWidget,
    QWidgetAction,
)

# Mapping: menu objectName -> list of related toolbar objectNames
MENU_TOOLBAR_MAP = {
    "mProjectMenu": ["mFileToolBar"],
    "mEditMenu": [
        "mDigitizeToolBar",
        "mAdvancedDigitizeToolBar",
        "mShapeDigitizeToolBar",
    ],
    "mViewMenu": ["mMapNavToolBar", "mAttributesToolBar"],
    "mLayerMenu": ["mLayerToolBar", "mDataSourceManagerToolBar"],
    "mSettingsMenu": [],
    "mPluginMenu": ["mPluginToolBar"],
    "mRasterMenu": ["mRasterToolBar"],
    "mVectorMenu": ["mVectorToolBar"],
    "processing": ["processingToolbar"],
    "mMeshMenu": ["mMeshToolBar"],
    "mDatabaseMenu": ["mDatabaseToolBar"],
    "mWebMenu": ["mWebToolBar"],
    "mHelpMenu": ["mHelpToolBar"],
}

# Tab ordering — controls the order tabs appear in the ribbon
TAB_ORDER = [
    "mProjectMenu",
    "mEditMenu",
    "mViewMenu",
    "mLayerMenu",
    "mSettingsMenu",
    "mRasterMenu",
    "mVectorMenu",
    "processing",
    "mMeshMenu",
    "mDatabaseMenu",
    "mWebMenu",
    "mPluginMenu",
    "mHelpMenu",
]

# Toolbar groups that count as "primary" (get large icons)
PRIMARY_TOOLBARS = {
    "mFileToolBar",
    "mMapNavToolBar",
    "mDigitizeToolBar",
    "mDataSourceManagerToolBar",
    "mSelectionToolBar",
}

MENU_POPUP_ACTIONS = {
    ("mProjectMenu", "New from Template"),
    ("mProjectMenu", "Open From"),
    ("mProjectMenu", "Open Recent"),
    ("mProjectMenu", "Save To"),
    ("mProjectMenu", "Import/Export"),
    ("mProjectMenu", "Layouts"),
    ("mProjectMenu", "Models"),
    ("mEditMenu", "Paste Features As"),
    ("mEditMenu", "Select"),
    ("mEditMenu", "Add Annotation"),
    ("mEditMenu", "Edit Attributes"),
    ("mEditMenu", "Edit Geometry"),
    ("mViewMenu", "3D Map Views"),
    ("mViewMenu", "Data Filtering"),
    ("mViewMenu", "Measure"),
    ("mViewMenu", "Decorations"),
    ("mViewMenu", "Preview Mode"),
    ("mViewMenu", "Layer Visibility"),
    ("mViewMenu", "Panels"),
    ("mViewMenu", "Toolbars"),
    ("mLayerMenu", "Create Layer"),
    ("mLayerMenu", "Add Layer"),
    ("mLayerMenu", "Filter Attribute Table"),
    ("mLayerMenu", "mActionAllEdits"),
    ("mSettingsMenu", "User Profiles"),
    ("mPluginMenu", "Plugin Reloader"),
    ("mPluginMenu", "QGIS MCP"),
    ("mPluginMenu", "qt6_compat"),
    ("mPluginMenu", "Ribbon Toolbar"),
    ("mRasterMenu", "Analysis"),
    ("mRasterMenu", "Projections"),
    ("mRasterMenu", "Miscellaneous"),
    ("mRasterMenu", "Extraction"),
    ("mRasterMenu", "Conversion"),
    ("mVectorMenu", "Analysis Tools"),
    ("mVectorMenu", "Geoprocessing Tools"),
    ("mVectorMenu", "Geometry Tools"),
    ("mVectorMenu", "Research Tools"),
    ("mVectorMenu", "Data Management Tools"),
    ("mHelpMenu", "Plugins"),
}

TOOLBAR_POPUP_ACTIONS = {
    ("mDigitizeToolBar", "mActionAllEdits"),
    ("mSnappingToolBar", "EnableTracingAction"),
}

WIDGET_POPUP_BUTTONS = {
    ("mAnnotationsToolBar", "mActionCreateAnnotationLayer"),
    ("mAttributesToolBar", "mActionFeatureAction"),
    ("mDigitizeToolBar", "mActionDigitizeWithSegment"),
    ("mGpsToolBar", "Set destination layer for GPS digitized features"),
    ("mGpsToolBar", "Settings"),
    ("mMeshToolBar", "Digitize Mesh Elements"),
    ("mMeshToolBar", "Force by Selected Geometries"),
    ("mPluginToolBar", "PluginReloader_ReloadRecentPlugin"),
    ("mShapeDigitizeToolBar", "Circle from 2 points"),
    ("mShapeDigitizeToolBar", "Ellipse from center and 2 points"),
    ("mShapeDigitizeToolBar", "Rectangle from center and a point"),
    ("mShapeDigitizeToolBar", "Regular polygon from 2 points"),
    ("mSnappingToolBar", "All Layers"),
    ("mSnappingToolBar", "Allow Overlap"),
    ("mSnappingToolBar", "Edit advanced configuration"),
    ("mSnappingToolBar", "Vertex"),
    ("processingToolbar", "Models"),
    ("processingToolbar", "Scripts"),
}

RIBBON_STYLESHEET = """
QTabWidget::pane {
    border: 1px solid #c4c4c4;
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #ffffff, stop:1 #f0f0f0);
    margin: 0px;
}
QTabWidget::tab-bar {
    alignment: left;
}
QTabBar::tab {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #f8f8f8, stop:1 #e0e0e0);
    border: 1px solid #c4c4c4;
    border-bottom: none;
    padding: 5px 14px;
    margin-right: 1px;
    font-size: 11px;
    font-weight: 500;
    min-width: 50px;
    color: #333;
}
QTabBar::tab:selected {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #ffffff, stop:1 #f0f0f0);
    border-bottom: 1px solid #ffffff;
    color: #0056b3;
    font-weight: 600;
}
QTabBar::tab:hover:!selected {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #e8f0fe, stop:1 #d0e0f8);
}
"""

GROUP_FRAME_STYLE = """
QFrame#ribbonGroup {
    border-right: 1px solid #d0d0d0;
    background: transparent;
    margin: 0px;
    padding: 0px 2px;
}
"""

GROUP_TITLE_STYLE = "color: #666; font-size: 9px; padding: 0px; margin-top: 1px;"


class RibbonWidget(QTabWidget):
    """Microsoft Office-like ribbon interface for QGIS."""

    def __init__(self, iface, parent=None):
        super().__init__(parent)
        self.iface = iface
        self.main_window = iface.mainWindow()
        self.setStyleSheet(RIBBON_STYLESHEET)
        self.setMinimumHeight(95)
        self.setMaximumHeight(120)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setUsesScrollButtons(True)
        self.setDocumentMode(False)

    def build_ribbon(self):
        """Populate the ribbon with tabs from QGIS menus and toolbars."""
        menubar = self.main_window.menuBar()
        all_toolbars = {}
        for tb in self.main_window.findChildren(QToolBar):
            name = tb.objectName()
            if name:
                all_toolbars[name] = tb

        # Collect top-level menus by objectName
        menus_by_name = {}
        for menu in menubar.findChildren(QMenu):
            if menu.parent() == menubar:
                menus_by_name[menu.objectName()] = menu

        # Collect plugin toolbars (toolbars not mapped to any menu)
        mapped_toolbars = set()
        for tb_list in MENU_TOOLBAR_MAP.values():
            mapped_toolbars.update(tb_list)
        mapped_toolbars.add("RibbonToolbarMain")

        # Additional known QGIS internal toolbars
        known_internal = {
            "mSnappingToolBar",
            "mLabelToolBar",
            "mAnnotationsToolBar",
            "mGpsToolBar",
            "mBookmarkToolbar",
            "mBrowserToolbar",
            "mSelectionToolBar",
            "mToolbar",
        }
        mapped_toolbars.update(known_internal)

        plugin_toolbars = []
        for name, tb in all_toolbars.items():
            if name not in mapped_toolbars and tb.actions():
                plugin_toolbars.append(tb)

        # Build tabs in order
        for menu_name in TAB_ORDER:
            menu = menus_by_name.get(menu_name)
            if menu is None:
                continue

            tab = self._build_tab(menu, all_toolbars, menu_name)
            clean_title = menu.title().replace("&", "")
            self.addTab(tab, clean_title)

        # "Extra" tab for additional toolbars (Snapping, Labels, Selection, etc.)
        extra_tab = self._build_extra_tab(all_toolbars)
        if extra_tab:
            self.addTab(extra_tab, "Tools")

        # "Plugins" tab additions — append plugin toolbars
        if plugin_toolbars:
            plugins_extra = self._build_plugins_extra_tab(plugin_toolbars)
            if plugins_extra:
                # We already added a Plugins tab from the menu;
                # find it and add groups
                pass  # handled in _build_tab for mPluginMenu

    def _build_tab(self, menu, all_toolbars, menu_name):
        """Build a single ribbon tab for a QGIS menu."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(2)

        # Add toolbar-based groups first
        related_toolbars = MENU_TOOLBAR_MAP.get(menu_name, [])
        for tb_name in related_toolbars:
            tb = all_toolbars.get(tb_name)
            if tb and tb.actions():
                is_primary = tb_name in PRIMARY_TOOLBARS
                title = tb.windowTitle() or tb_name
                group = self._create_group(
                    title,
                    tb.actions(),
                    large=is_primary,
                    source_kind="toolbar",
                    source_name=tb_name,
                )
                layout.addWidget(group)

        # If this is the Plugins menu tab, also add plugin toolbars
        if menu_name == "mPluginMenu":
            mapped_toolbars = set()
            for tb_list in MENU_TOOLBAR_MAP.values():
                mapped_toolbars.update(tb_list)
            mapped_toolbars.add("RibbonToolbarMain")
            known_internal = {
                "mSnappingToolBar",
                "mLabelToolBar",
                "mAnnotationsToolBar",
                "mGpsToolBar",
                "mBookmarkToolbar",
                "mBrowserToolbar",
                "mSelectionToolBar",
                "mToolbar",
            }
            mapped_toolbars.update(known_internal)
            for tb in self.main_window.findChildren(QToolBar):
                name = tb.objectName()
                if name and name not in mapped_toolbars and tb.actions():
                    group = self._create_group(
                        tb.windowTitle() or name,
                        tb.actions(),
                        large=False,
                        source_kind="toolbar",
                        source_name=name,
                    )
                    layout.addWidget(group)

        # Add menu actions as a group
        menu_actions = [a for a in menu.actions() if not a.isSeparator()]
        if menu_actions:
            clean_title = menu.title().replace("&", "") + " Menu"
            group = self._create_group(
                clean_title,
                menu_actions,
                large=False,
                source_kind="menu",
                source_name=menu_name,
            )
            layout.addWidget(group)

        layout.addStretch()
        scroll.setWidget(container)
        return scroll

    def _build_extra_tab(self, all_toolbars):
        """Build the 'Tools' tab for additional QGIS toolbars."""
        extra_names = [
            ("mSnappingToolBar", "Snapping"),
            ("mLabelToolBar", "Labels"),
            ("mSelectionToolBar", "Selection"),
            ("mAnnotationsToolBar", "Annotations"),
            ("mGpsToolBar", "GPS"),
        ]
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(2)

        has_content = False
        for tb_name, title in extra_names:
            tb = all_toolbars.get(tb_name)
            if tb and tb.actions():
                group = self._create_group(
                    title,
                    tb.actions(),
                    large=False,
                    source_kind="toolbar",
                    source_name=tb_name,
                )
                layout.addWidget(group)
                has_content = True

        layout.addStretch()
        if has_content:
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.NoFrame)
            scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            scroll.setWidget(container)
            return scroll
        return None

    def _build_plugins_extra_tab(self, plugin_toolbars):
        """Build additional groups for plugin toolbars."""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(2)
        for tb in plugin_toolbars:
            title = tb.windowTitle() or tb.objectName()
            group = self._create_group(
                title,
                tb.actions(),
                large=False,
                source_kind="toolbar",
                source_name=tb.objectName(),
            )
            layout.addWidget(group)
        layout.addStretch()
        return container

    def _create_group(self, title, actions, large=False, source_kind=None, source_name=None):
        """Create a ribbon group: a framed section with buttons and a title."""
        group = QFrame()
        group.setObjectName("ribbonGroup")
        group.setStyleSheet(GROUP_FRAME_STYLE)

        main_layout = QVBoxLayout(group)
        main_layout.setContentsMargins(4, 2, 4, 0)
        main_layout.setSpacing(0)

        if large:
            btn_layout = QHBoxLayout()
            btn_layout.setSpacing(2)
            for action in actions:
                if action.isSeparator():
                    # Visual separator
                    sep = QFrame()
                    sep.setFrameShape(QFrame.VLine)
                    sep.setFrameShadow(QFrame.Sunken)
                    sep.setFixedWidth(1)
                    btn_layout.addWidget(sep)
                    continue
                if isinstance(action, QWidgetAction):
                    dw = action.defaultWidget()
                    if dw is not None:
                        btn = self._clone_widget_button(
                            dw,
                            large=True,
                            source_name=source_name,
                            parent=group,
                        )
                        if btn is not None:
                            btn_layout.addWidget(btn)
                    continue
                btn = self._make_button(
                    action,
                    large=True,
                    source_kind=source_kind,
                    source_name=source_name,
                    parent=group,
                )
                btn_layout.addWidget(btn)
            main_layout.addLayout(btn_layout)
        else:
            # Small buttons arranged in a grid (up to 3 rows)
            grid = QGridLayout()
            grid.setSpacing(1)
            grid.setContentsMargins(0, 0, 0, 0)
            row, col = 0, 0
            for action in actions:
                if action.isSeparator():
                    # Move to next column if we have items
                    if row > 0:
                        col += 1
                        row = 0
                    continue
                if isinstance(action, QWidgetAction):
                    dw = action.defaultWidget()
                    if dw is not None:
                        btn = self._clone_widget_button(
                            dw,
                            large=False,
                            source_name=source_name,
                            parent=group,
                        )
                        if btn is not None:
                            grid.addWidget(btn, row, col)
                            row += 1
                            if row >= 3:
                                row = 0
                                col += 1
                    continue
                btn = self._make_button(
                    action,
                    large=False,
                    source_kind=source_kind,
                    source_name=source_name,
                    parent=group,
                )
                grid.addWidget(btn, row, col)
                row += 1
                if row >= 3:
                    row = 0
                    col += 1
            main_layout.addLayout(grid)

        # Group title at bottom
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet(GROUP_TITLE_STYLE)
        main_layout.addWidget(title_label)

        return group

    def _clean_text(self, text):
        return re.sub(r"<[^>]+>", "", (text or "").replace("&", "")).strip()

    def _action_popup_id(self, action):
        return action.objectName() or self._clean_text(action.text())

    def _widget_popup_id(self, source):
        default_action = source.defaultAction()
        if default_action and default_action.objectName():
            return default_action.objectName()
        if default_action and self._clean_text(default_action.text()):
            return self._clean_text(default_action.text())
        if self._clean_text(source.text()):
            return self._clean_text(source.text())
        if self._clean_text(source.toolTip()):
            return self._clean_text(source.toolTip())
        return ""

    def _is_popup_action(self, source_kind, source_name, action):
        action_key = (source_name, self._action_popup_id(action))
        if source_kind == "menu":
            return action_key in MENU_POPUP_ACTIONS
        if source_kind == "toolbar":
            return action_key in TOOLBAR_POPUP_ACTIONS
        return False

    def _is_popup_widget_button(self, source_name, source):
        return (source_name, self._widget_popup_id(source)) in WIDGET_POPUP_BUTTONS

    def _clone_widget_button(self, source, large=False, source_name=None, parent=None):
        """Clone a QToolButton from a QWidgetAction's defaultWidget.
        Returns None for non-QToolButton widgets (spinboxes, etc.)."""
        if not isinstance(source, QToolButton):
            return None
        clone = QToolButton(parent)
        clone.setIcon(source.icon())
        clone.setToolTip(source.toolTip())
        clone.setAutoRaise(True)
        if self._is_popup_widget_button(source_name, source):
            clone.setMenu(source.menu())
            clone.setPopupMode(source.popupMode())
        # Wire click through to the hidden original so all internal logic fires
        clone.clicked.connect(source.click)
        if large:
            clone.setIconSize(QSize(28, 28))
            clone.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
            clone.setFixedSize(56, 70)
        else:
            clone.setIconSize(QSize(18, 18))
            if source.icon().isNull():
                clone.setToolButtonStyle(Qt.ToolButtonTextOnly)
            else:
                clone.setToolButtonStyle(Qt.ToolButtonIconOnly)
            clone.setFixedHeight(22)
        return clone

    def _sync_menu_button(self, button, action):
        """Keep a popup-only menu button aligned with its source action."""
        if sip.isdeleted(button):
            return
        button.setText(self._clean_text(action.text()))
        button.setIcon(action.icon())
        button.setToolTip(self._clean_text(action.toolTip()) or self._clean_text(action.text()))
        button.setStatusTip(action.statusTip())
        button.setEnabled(action.isEnabled())
        button.setVisible(action.isVisible())

    def _sync_popup_menu(self, popup_menu, source_menu):
        """Mirror the current actions from a source menu into a detached popup."""
        popup_menu.clear()
        popup_menu.addActions(source_menu.actions())

    def _make_button(self, action, large=False, source_kind=None, source_name=None, parent=None):
        """Create a QToolButton for a ribbon action."""
        btn = QToolButton(parent)
        btn.setAutoRaise(True)

        if self._is_popup_action(source_kind, source_name, action):
            source_menu = action.menu()
            self._sync_menu_button(btn, action)
            popup_menu = QMenu(btn)
            self._sync_popup_menu(popup_menu, source_menu)
            popup_menu.aboutToShow.connect(
                lambda popup_menu=popup_menu, action=action: self._sync_popup_menu(
                    popup_menu, action.menu()
                )
            )
            btn.setMenu(popup_menu)
            btn.setPopupMode(QToolButton.InstantPopup)
            action.changed.connect(
                lambda btn=btn, action=action: self._sync_menu_button(btn, action)
            )
        else:
            btn.setDefaultAction(action)

        if large:
            btn.setIconSize(QSize(28, 28))
            btn.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
            btn.setFixedSize(56, 70)
        else:
            btn.setIconSize(QSize(18, 18))
            if action.icon() and not action.icon().isNull():
                btn.setToolButtonStyle(Qt.ToolButtonIconOnly)
            else:
                btn.setToolButtonStyle(Qt.ToolButtonTextOnly)
                btn.setMaximumWidth(120)
            btn.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
            btn.setFixedHeight(22)

        return btn

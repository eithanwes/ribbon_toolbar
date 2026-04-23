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
    "mSelectionMenu",  # Special virtual menu for Selection actions
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
LARGE_ICONS = {
    "mFileToolBar",
    "mMapNavToolBar",
    "mDigitizeToolBar",
    "mDataSourceManagerToolBar",
    "mSelectionToolBar",
    "mSettingsMenu",
    "processingToolbar",
    "processing",
    "mPluginMenu",
    "mPluginToolBar",
    "mSelectionMenu",
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
        all_toolbars = self._collect_all_toolbars()
        menus_by_name = self._collect_menus_by_name(menubar)

        # Build tabs in order
        for menu_name in TAB_ORDER:
            if menu_name == "mSelectionMenu":
                self._build_selection_menu_tab(menus_by_name)
                continue

            self._build_standard_menu_tab(menu_name, menus_by_name, all_toolbars)

        # "Extra" tab for additional toolbars (Snapping, Labels, Selection, etc.)
        extra_tab = self._build_extra_tab(all_toolbars)
        if extra_tab:
            self.addTab(extra_tab, "Tools")

    def _collect_all_toolbars(self):
        """Collect all toolbars from the main window."""
        all_toolbars = {}
        for tb in self.main_window.findChildren(QToolBar):
            name = tb.objectName()
            if name:
                all_toolbars[name] = tb
        return all_toolbars

    def _collect_menus_by_name(self, menubar):
        """Collect top-level menus by objectName."""
        menus_by_name = {}
        for menu in menubar.findChildren(QMenu):
            if menu.parent() == menubar:
                menus_by_name[menu.objectName()] = menu
        return menus_by_name

    def _get_mapped_toolbars_set(self):
        """Get the set of all toolbar names that are mapped to menus."""
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
        return mapped_toolbars

    def _collect_plugin_toolbars(self, all_toolbars):
        """Collect toolbars not mapped to any menu."""
        mapped_toolbars = self._get_mapped_toolbars_set()
        plugin_toolbars = []
        for name, tb in all_toolbars.items():
            if name not in mapped_toolbars and tb.actions():
                plugin_toolbars.append(tb)
        return plugin_toolbars

    def _build_selection_menu_tab(self, menus_by_name):
        """Build the virtual Selection menu tab."""
        edit_menu = menus_by_name.get("mEditMenu")
        if not edit_menu:
            return

        for action in edit_menu.actions():
            submenu = action.menu()
            if (
                action.isSeparator()
                or self._clean_text(action.text()) != "Select"
                or not submenu
            ):
                continue
            tab = self._build_selection_tab(submenu)
            self.addTab(tab, "Selection")
            return

    def _build_standard_menu_tab(self, menu_name, menus_by_name, all_toolbars):
        """Build a standard menu tab."""
        menu = menus_by_name.get(menu_name)
        if menu is None:
            return

        tab = self._build_tab(menu, all_toolbars, menu_name)
        clean_title = menu.title().replace("&", "")
        self.addTab(tab, clean_title)

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

        # Track action identities and toolbar-only actions
        seen_ids = set()
        empty_toolbar_action_ids = set()

        # Add toolbar-based groups first
        self._add_toolbar_groups(
            layout,
            menu_name,
            all_toolbars,
            seen_ids,
            empty_toolbar_action_ids,
        )

        # If this is the Plugins menu tab, also add plugin toolbars
        if menu_name == "mPluginMenu":
            self._add_plugin_toolbars_to_tab(layout, seen_ids)

        # Add menu actions as a group
        self._add_menu_group(
            layout, menu, menu_name, seen_ids, empty_toolbar_action_ids
        )

        layout.addStretch()
        scroll.setWidget(container)
        return scroll

    def _add_toolbar_groups(
        self, layout, menu_name, all_toolbars, seen_ids, empty_toolbar_action_ids
    ):
        """Add toolbar-based groups to the tab layout."""
        related_toolbars = MENU_TOOLBAR_MAP.get(menu_name, [])
        for tb_name in related_toolbars:
            tb = all_toolbars.get(tb_name)
            if not tb or not tb.actions():
                continue
            is_primary = tb_name in LARGE_ICONS
            title = tb.windowTitle() or tb_name
            group = self._create_group(
                title,
                tb.actions(),
                large=is_primary,
                source_kind="toolbar",
                source_name=tb_name,
            )
            layout.addWidget(group)
            self._track_toolbar_actions(tb, seen_ids, empty_toolbar_action_ids)

    def _track_toolbar_actions(self, toolbar, seen_ids, empty_toolbar_action_ids):
        """Track which actions are from toolbars and which have no text."""
        for a in toolbar.actions():
            if a.isSeparator():
                continue
            action_id = id(a)
            seen_ids.add(action_id)
            if not self._clean_text(a.text()):
                empty_toolbar_action_ids.add(action_id)

    def _add_plugin_toolbars_to_tab(self, layout, seen_ids):
        """Add plugin toolbars to the Plugins menu tab."""
        mapped_toolbars = self._get_mapped_toolbars_set()
        for tb in self.main_window.findChildren(QToolBar):
            name = tb.objectName()
            if not name or name in mapped_toolbars or not tb.actions():
                continue
            group = self._create_group(
                tb.windowTitle() or name,
                tb.actions(),
                large=False,
                source_kind="toolbar",
                source_name=name,
            )
            layout.addWidget(group)
            for a in tb.actions():
                if a.isSeparator():
                    continue
                seen_ids.add(id(a))

    def _add_menu_group(
        self,
        layout,
        menu,
        menu_name,
        seen_ids,
        empty_toolbar_action_ids,
    ):
        """Add menu actions as a group, excluding actions already shown by toolbars."""
        menu_actions = [
            a
            for a in menu.actions()
            if not a.isSeparator()
            and (id(a) not in seen_ids or id(a) in empty_toolbar_action_ids)
        ]
        if menu_actions:
            clean_title = menu.title().replace("&", "") + " Menu"
            group = self._create_group(
                clean_title,
                menu_actions,
                large=menu_name in LARGE_ICONS,
                source_kind="menu",
                source_name=menu_name,
            )
            layout.addWidget(group)

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
            if not tb or not tb.actions():
                continue
            is_primary = tb_name in LARGE_ICONS
            group = self._create_group(
                title,
                tb.actions(),
                large=is_primary,
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

    def _build_selection_tab(self, selection_menu):
        """Build the Selection tab from the Edit > Select submenu."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(2)

        # Create a single group with all selection actions
        group = self._create_group(
            "Selection",
            selection_menu.actions(),
            large=True,
            source_kind="menu",
            source_name="mSelectionMenu",
        )
        layout.addWidget(group)
        layout.addStretch()
        scroll.setWidget(container)
        return scroll

    def _create_group(
        self, title, actions, large=False, source_kind=None, source_name=None
    ):
        """Create a ribbon group: a framed section with buttons and a title."""
        group = QFrame()
        group.setObjectName("ribbonGroup")
        group.setStyleSheet(GROUP_FRAME_STYLE)

        main_layout = QVBoxLayout(group)
        main_layout.setContentsMargins(4, 2, 4, 0)
        main_layout.setSpacing(0)

        if large:
            btn_layout = self._create_large_button_layout(
                actions, source_kind, source_name, group
            )
            main_layout.addLayout(btn_layout)
        else:
            grid = self._create_small_button_grid(
                actions, source_kind, source_name, group
            )
            main_layout.addLayout(grid)

        # Group title at bottom
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet(GROUP_TITLE_STYLE)
        main_layout.addWidget(title_label)

        return group

    def _create_large_button_layout(self, actions, source_kind, source_name, parent):
        """Create a horizontal layout with large buttons."""
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(2)
        for action in actions:
            if action.isSeparator():
                self._add_separator_to_layout(btn_layout)
                continue
            if isinstance(action, QWidgetAction):
                self._add_widget_action_to_layout(
                    btn_layout,
                    action,
                    large=True,
                    source_name=source_name,
                    parent=parent,
                )
                continue
            btn = self._make_button(
                action,
                large=True,
                source_kind=source_kind,
                source_name=source_name,
                parent=parent,
            )
            btn_layout.addWidget(btn)
        return btn_layout

    def _create_small_button_grid(self, actions, source_kind, source_name, parent):
        """Create a grid layout with small buttons (up to 3 rows)."""
        grid = QGridLayout()
        grid.setSpacing(1)
        grid.setContentsMargins(0, 0, 0, 0)
        row, col = 0, 0
        for action in actions:
            if action.isSeparator() and row > 0:
                col += 1
                row = 0
                continue
            if isinstance(action, QWidgetAction):
                row, col = self._add_widget_action_to_grid(
                    grid, action, row, col, source_name=source_name, parent=parent
                )
                continue
            btn = self._make_button(
                action,
                large=False,
                source_kind=source_kind,
                source_name=source_name,
                parent=parent,
            )
            grid.addWidget(btn, row, col)
            row += 1
            if row >= 3:
                row = 0
                col += 1
        return grid

    def _add_separator_to_layout(self, layout):
        """Add a vertical separator line to a layout."""
        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setFrameShadow(QFrame.Sunken)
        sep.setFixedWidth(1)
        layout.addWidget(sep)

    def _add_widget_action_to_layout(
        self, layout, action, large=False, source_name=None, parent=None
    ):
        """Add a widget action button to a horizontal layout."""
        dw = action.defaultWidget()
        if dw is None:
            return
        btn = self._clone_widget_button(
            dw,
            large=large,
            source_name=source_name,
            parent=parent,
        )
        if btn is None:
            return
        layout.addWidget(btn)

    def _add_widget_action_to_grid(
        self, grid, action, row, col, source_name=None, parent=None
    ):
        """Add a widget action button to a grid layout and return updated row/col."""
        dw = action.defaultWidget()
        if dw is None:
            return row, col
        btn = self._clone_widget_button(
            dw,
            large=False,
            source_name=source_name,
            parent=parent,
        )
        if btn is None:
            return row, col
        grid.addWidget(btn, row, col)
        row += 1
        if row >= 3:
            row = 0
            col += 1
        return row, col

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
        popup_actions = {
            "menu": MENU_POPUP_ACTIONS,
            "toolbar": TOOLBAR_POPUP_ACTIONS,
        }.get(source_kind)
        if not popup_actions:
            return False
        return action_key in popup_actions

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
        button.setToolTip(
            self._clean_text(action.toolTip()) or self._clean_text(action.text())
        )
        button.setStatusTip(action.statusTip())
        button.setEnabled(action.isEnabled())
        button.setVisible(action.isVisible())

    def _sync_popup_menu(self, popup_menu, source_menu):
        """Mirror the current actions from a source menu into a detached popup."""
        popup_menu.clear()
        popup_menu.addActions(source_menu.actions())

    def _make_button(
        self, action, large=False, source_kind=None, source_name=None, parent=None
    ):
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

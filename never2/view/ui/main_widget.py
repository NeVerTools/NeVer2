"""
Module main_widget.py

This module contains the QWidget class EditorWidget.

Author: Andrea Gimelli, Giacomo Rosato, Stefano Demarchi

"""

from functools import partial
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QTreeWidget, QTreeWidgetItem, QSplitter, QPushButton, QFileDialog, \
    QApplication

import never2.utils.rep as rep
from never2 import RES_DIR
from never2.model.component.block import LayerBlock, PropertyBlock
from never2.model.project import Project
from never2.model.scene import Scene
from never2.utils.file import FileFormat, read_properties
from never2.view.component.inspector import InspectorDockToolbar
from never2.view.ui.dialog import MessageDialog, MessageType, ConfirmDialog


class EditorWidget(QWidget):
    """
    This class initializes the main layout of the application containing the toolbar
    on the left and the scene on the right.

    """

    def __init__(self, main_window: 'MainWindow', parent=None):
        super().__init__(parent)

        # Reference to the main window
        self.main_wnd_ref = main_window

        # Style
        with open(RES_DIR + '/styling/qss/style.qss') as qss_file:
            self.setStyleSheet(qss_file.read())

        # Widget layout
        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

        self.splitter = QSplitter(self)
        self.splitter.setOrientation(Qt.Orientation.Horizontal)
        self.layout.addWidget(self.splitter)

        # Objects data from JSON
        self.block_data, self.property_data, self.functional_data = rep.read_json_data()

        # Layers toolbar
        self.layers_toolbar = self.create_layers_toolbar()
        self.inspector = InspectorDockToolbar(self.block_data, self.property_data)
        self.main_wnd_ref.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.inspector)

        # Scene
        self.scene = Scene(self)

    def create_layers_toolbar(self) -> QTreeWidget:
        """
        This method creates a QTreeWidget object reading values from block_data

        """

        toolbar_tree = QTreeWidget()
        toolbar_tree.setHeaderHidden(True)

        for i in self.block_data.keys():
            i_item = QTreeWidgetItem([i])
            toolbar_tree.addTopLevelItem(i_item)

            for j in self.block_data[i].keys():
                j_item = QTreeWidgetItem(i_item, [j])
                button = QPushButton(j)  # TODO refactor style in order to use a CustomButton
                dict_sign = i + ':' + j
                draw_part = partial(self.add_block_proxy, self.block_data[i][j], dict_sign)
                button.clicked.connect(draw_part)
                toolbar_tree.setItemWidget(j_item, 0, button)

        # Size control
        toolbar_tree.setMinimumWidth(250)
        toolbar_tree.setMaximumWidth(400)
        toolbar_tree.expandAll()

        self.splitter.addWidget(toolbar_tree)
        return toolbar_tree

    def add_block_proxy(self, block_data: dict, block_sign: str):
        """
        Proxy method to add a node in the scene

        """

        self.scene.add_layer_block(block_data, block_sign)

    def save_prompt_dialog(self) -> Optional[ConfirmDialog]:
        """
        This method opens a dialog for asking to save the work

        """

        dialog = None

        if self.scene.project.is_modified():
            dialog = ConfirmDialog('Confirmation required',
                                   'There are unsaved changes. Save current work before exit?')
            dialog.set_buttons_text('Discard changes', 'Save')
            dialog.exec()

            if dialog.confirm:
                self.save()

        return dialog

    def new(self):
        """
        This method clears the workspace and creates a new project

        """

        self.save_prompt_dialog()
        self.scene.clear_scene()
        self.scene.project = Project(self.scene)

        self.main_wnd_ref.set_project_title('')

    def open(self):
        """
        This method loads a network from a file and draws it

        """

        try:
            self.save_prompt_dialog()

            filename = QFileDialog.getOpenFileName(None, 'Open network', '', FileFormat.NETWORK_FORMATS_OPENING)

            if filename != ('', ''):
                self.clear()
                self.scene.project = Project(self.scene, filename)

                filename_reduced = filename[0].split('/')[-1]
                self.main_wnd_ref.set_project_title(filename_reduced)

        except Exception as e:
            dialog = MessageDialog(f'Error: {str(e)}', MessageType.ERROR)
            dialog.exec()

    def open_property(self):
        """
        This method loads a SMT property associated to the network

        """

        try:
            if self.scene.project.nn.is_empty():
                dialog = MessageDialog('No network loaded', MessageType.ERROR)
                dialog.exec()

            else:
                filename = QFileDialog.getOpenFileName(None, 'Open property', '', FileFormat.PROPERTY_FORMATS)

                if filename != ('', ''):
                    QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
                    properties = read_properties(filename[0])
                    QApplication.restoreOverrideCursor()

                    self.scene.load_properties(properties)

        except Exception as e:
            dialog = MessageDialog(f'Error: {str(e)}', MessageType.ERROR)
            dialog.exec()

    def save(self, _as: bool = False):
        """
        This method saves the current network in the window

        """

        try:
            success = self.scene.project.save(_as)

            if success:
                filename_reduced = self.scene.project.filename[0].split('/')[-1]
                self.main_wnd_ref.set_project_title(filename_reduced)
        except Exception as e:
            dialog = MessageDialog(f'Error: {str(e)}', MessageType.ERROR)
            dialog.exec()

    def clear(self):
        """
        This method clears the workspace in order to start from scratch

        """

        self.scene.clear_scene()
        self.scene.project.reset_nn('X', 'INP')

    def remove_sel(self):
        """
        This method tries to delete the element selected, if allowed

        """

        self.scene.view.check_delete()

    def show_inspector(self):
        """
        This method opens the block inspector if a block is selected

        """

        if len(self.scene.graphics_scene.selectedItems()) == 1:
            item = self.scene.graphics_scene.selectedItems()

            if hasattr(item[0], 'block_ref'):
                if isinstance(item[0].block_ref, LayerBlock) or isinstance(item[0].block_ref, PropertyBlock):
                    self.inspector.display(item[0].block_ref)

import itertools
import json
from typing import Optional

from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QStatusBar, QAction, QGraphicsRectItem, QPushButton

import never2.view.styles as style
from never2 import ROOT_DIR
from never2.view.drawing.element import GraphicLine, NodeBlock
from never2.view.drawing.scene import DrawingMode, Canvas
from never2.view.widget.custom import CustomLabel
from never2.view.widget.dialog.dialogs import ConfirmDialog, MessageDialog, MessageType, HelpDialog
from never2.view.widget.toolbar import BlocksToolbar, NodeButton, PropertyButton
from never2.view.widget.toolbar import ParamToolbar


class MainWindow(QtWidgets.QMainWindow):
    """
    This class is the main window of the program, containing all the graphics
    objects such as the toolbar, the state bar, the menu and the canvas scene.

    Attributes
    ----------
    SYSNAME : str
        The application name displayed in the window.
    nav_menu_bar : QMenuBar
        Menu bar of the window, containing different menus.
    status_bar : QStatusBar
        Status bar of the window.
    toolbar : BlocksToolbar
        Toolbar appearing on the left of the window, showing several buttons to
        add elements to the canvas.
    parameters : ParamToolbar
        Fixed toolbar on the right of the window, displaying details about a
        certain block.
    canvas : Canvas
        Central view of the window, containing a blank space in which the
        blocks appear.

    Methods
    ----------
    connect_events()
        Connects to all signals of the elements.
    init_menu_bar()
        Sets all menus of the menu bar and their actions.
    update_status()
        Changes the status bar displaying on it the canvas mode and the
        selected items.
    change_draw_mode(DrawingMode)
        Changes the drawing mode of the canvas.
    create_from(NodeButton)
        Draws in the canvas the block corresponding to the button pressed.
    reset()
        Clears both graphical and logical network.
    open()
        Procedure to open an existing network.
    save(bool)
        Saves the current network in a new file or in the opened one.

    """

    def __init__(self):
        super(MainWindow, self).__init__()

        # Init window appearance
        self.SYSNAME = "NeVer 2"
        self.setWindowTitle(self.SYSNAME)
        self.setWindowIcon(QtGui.QIcon(ROOT_DIR + '/res/icons/logo.png'))
        self.setStyleSheet("background-color: " + style.GREY_1)

        # Navigation menu
        self.nav_menu_bar = self.menuBar()
        self.init_nav_menu_bar()

        # Blocks toolbar
        self.toolbar = BlocksToolbar(ROOT_DIR + '/res/json/blocks.json')

        # Parameters toolbar
        self.parameters = ParamToolbar()

        # Drawing Canvas
        self.canvas = Canvas(self.toolbar.blocks)

        # Status bar
        self.status_bar = QStatusBar()
        self.status_bar.setSizeGripEnabled(False)
        self.setStatusBar(self.status_bar)
        self.status_bar.setStyleSheet(style.STATUS_BAR_STYLE)
        self.status_bar_mode_label = CustomLabel()
        self.status_bar_mode_label.setStyleSheet(style.STATUS_BAR_WIDGET_STYLE)
        self.status_bar_selections_label = CustomLabel()
        self.status_bar_selections_label.setStyleSheet(style.STATUS_BAR_WIDGET_STYLE)
        self.status_bar.addPermanentWidget(self.status_bar_selections_label)
        self.status_bar.addPermanentWidget(self.status_bar_mode_label)

        # And adding them to the window
        self.addDockWidget(Qt.RightDockWidgetArea, self.parameters, Qt.Vertical)
        self.addToolBar(QtCore.Qt.ToolBarArea.LeftToolBarArea, self.toolbar)
        self.setCentralWidget(self.canvas.view)

        self.connect_events()

    def connect_events(self):
        """
        Associate the various events coming from button signals and other
        graphical objects to the correct actions.

        """

        # Block buttons
        for b in itertools.chain(self.toolbar.b_buttons.values(),
                                 self.toolbar.p_buttons.values()):
            b.clicked.connect(self.create_from(b))

        # Draw line button
        self.toolbar.f_buttons["draw_line"].clicked \
            .connect(lambda: self.change_draw_mode(DrawingMode.DRAW_LINE))

        # Insert block button
        self.toolbar.f_buttons["insert_block"].clicked \
            .connect(lambda: self.change_draw_mode(DrawingMode.DRAW_BLOCK))

        # Parameters box appearing
        self.canvas.param_requested \
            .connect(lambda: self.parameters.display(self.canvas.block_to_show))

        # State bar updating
        self.canvas.scene.has_changed_mode \
            .connect(lambda: self.update_status())
        self.canvas.scene.selectionChanged \
            .connect(lambda: self.update_status())

    def init_nav_menu_bar(self):
        """
        This method creates the navigation bar by adding the menus and
        corresponding actions.

        """

        self.nav_menu_bar.setStyleSheet(style.MENU_BAR_STYLE)
        self.setContextMenuPolicy(Qt.PreventContextMenu)
        actions_dict = dict()

        with open(ROOT_DIR + '/res/json/menu.json') as json_menu:
            menu = json.loads(json_menu.read())

        for menu_item, actions in menu.items():
            entry = self.nav_menu_bar.addMenu(menu_item)
            entry.setStyleSheet(style.MENU_BAR_STYLE)

            for a, v in actions.items():
                action_item = QAction(a, self)
                if "Shortcut" in v.keys():
                    action_item.setShortcut(v["Shortcut"])
                if v["checkable"] == "True":
                    action_item.setCheckable(True)
                    action_item.setChecked(True)
                entry.addAction(action_item)
                actions_dict[f"{menu_item}:{a}"] = action_item

        # Triggers connection
        actions_dict["File:New..."].triggered.connect(lambda: self.reset())
        actions_dict["File:Open..."].triggered.connect(lambda: self.open())
        actions_dict["File:Load property..."].triggered.connect(lambda: self.canvas.project.open_property())
        actions_dict["File:Save"].triggered.connect(lambda: self.save(False))
        actions_dict["File:Save as..."].triggered.connect(lambda: self.save())
        actions_dict["File:Exit"].triggered.connect(lambda: self.close())

        actions_dict["Edit:Copy"].triggered.connect(lambda: self.canvas.copy_selected())
        actions_dict["Edit:Paste"].triggered.connect(lambda: self.canvas.paste_selected())
        actions_dict["Edit:Cut"].triggered.connect(lambda: self.canvas.cut_selected())
        actions_dict["Edit:Delete"].triggered.connect(lambda: self.canvas.delete_selected())
        actions_dict["Edit:Clear canvas"].triggered.connect(lambda: self.clear())
        actions_dict["Edit:Draw connection"].triggered.connect(lambda: self.change_draw_mode(DrawingMode.DRAW_LINE))
        actions_dict["Edit:Edit node"].triggered.connect(
            lambda: self.canvas.scene.edit_node(self.edit_action_validation()))

        actions_dict["View:Zoom in"].triggered.connect(lambda: self.canvas.zoom_in())
        actions_dict["View:Zoom out"].triggered.connect(lambda: self.canvas.zoom_out())
        actions_dict["View:Dimensions"].toggled.connect(lambda: self.canvas.scene.switch_dim_visibility())
        actions_dict["View:Tools"].toggled.connect(lambda: self.toolbar.change_tools_mode())
        actions_dict["View:Blocks"].toggled.connect(lambda: self.toolbar.change_blocks_mode())
        actions_dict["View:Parameters"].triggered.connect(
            lambda: self.canvas.show_parameters(self.parameters_action_validation()))

        actions_dict["Learning:Train..."].triggered.connect(lambda: self.canvas.train_network())
        actions_dict["Learning:Prune..."].triggered.connect(lambda: self.temp_window())

        actions_dict["Verification:Verify..."].triggered.connect(lambda: self.canvas.verify_network())
        actions_dict["Verification:Repair..."].triggered.connect(lambda: self.temp_window())

        actions_dict["Help:Show guide"].triggered.connect(lambda: self.show_help())

    @staticmethod
    def temp_window():
        dialog = MessageDialog("Work in progress...", MessageType.MESSAGE)
        dialog.exec()

    def create_from(self, button: QPushButton):
        """
        This method draws on the canvas the block corresponding to the pressed
        BlockButton.

        Parameters
        ----------
        button : CustomButton
            The pressed button.

        """

        def pressed():
            if isinstance(button, NodeButton):
                self.canvas.draw_node(button.node_type)
            elif isinstance(button, PropertyButton):
                if self.canvas.project.network.nodes:
                    self.canvas.draw_property(button.name)

        return pressed

    def update_status(self):
        """
        This method updates the widget in the status bar, displaying the
        items selected and the current drawing mode.

        """

        # Show the canvas drawing mode
        if self.canvas.scene.mode == DrawingMode.DRAW_LINE:
            self.status_bar_mode_label.setText("GraphicLine drawing")
        elif self.canvas.scene.mode == DrawingMode.DRAW_BLOCK:
            self.status_bar_mode_label.setText("Block insertion")
        else:
            self.status_bar_mode_label.setText("")

        # Show the selected items, if any
        if not self.canvas.scene.selectedItems():
            self.status_bar_selections_label.setText("")
        else:
            selections = ""
            semicolons = ["; " for _ in range(len(self.canvas.scene.selectedItems()))]
            semicolons[-1] = ""  # No semicolon for the last element in the selections list

            for counter, item in enumerate(self.canvas.scene.selectedItems()):
                if type(item) is QGraphicsRectItem:
                    # If the item is a rect, prev_node_id is written
                    selections += self.canvas.scene.blocks[item].block_id
                    selections += semicolons[counter]
                elif type(item) is GraphicLine:
                    # If the item is a line, origin and destination ids are written
                    origin = self.canvas.scene.blocks[item.origin].block_id
                    destination = self.canvas.scene.blocks[item.destination].block_id
                    selections += origin + "->" + destination
                    selections += semicolons[counter]

            self.status_bar_selections_label.setText(selections)

    def change_draw_mode(self, newmode: DrawingMode = None):
        """
        This method changes the drawing mode of the canvas when the user
        clicks on the corresponding button. The mode changes depending
        on the previous one.

        Parameters
        ----------
        newmode : DrawingMode, optional
            Specifies the new DrawingMode to use. (Default: None)

        """

        if newmode is None:
            self.canvas.scene.set_mode(DrawingMode.IDLE)
        else:
            curmode = self.canvas.scene.mode
            if newmode == curmode:
                self.canvas.scene.set_mode(DrawingMode.IDLE)
            else:
                self.canvas.scene.set_mode(newmode)

    def clear(self):
        """
        Utility for deleting the content of the window. Before taking effect,
        it prompts the user to confirm.

        """

        if self.canvas.num_nodes > 0:
            alert_dialog = ConfirmDialog("Clear workspace",
                                         "The network will be erased and your work will be lost.\n"
                                         "Do you wish to continue?")
            alert_dialog.exec()
            if alert_dialog.confirm:
                self.canvas.clear_scene()
                self.canvas.scene.has_changed_mode.connect(lambda: self.update_status())
                self.canvas.scene.selectionChanged.connect(lambda: self.update_status())
                self.update_status()
                self.setWindowTitle(self.SYSNAME)
        else:
            self.canvas.clear_scene()
            self.canvas.scene.has_changed_mode.connect(lambda: self.update_status())
            self.canvas.scene.selectionChanged.connect(lambda: self.update_status())
            self.update_status()
            self.setWindowTitle(self.SYSNAME)

    def reset(self):
        """
        This method clears the scene and the network, stops to work on the file
        and restarts from scratch.

        """

        self.clear()
        self.canvas.project.file_name = ("", "")
        self.setWindowTitle(self.SYSNAME)

    def open(self):
        """
        This method handles the opening of a file.

        """

        if self.canvas.renderer.disconnected_network:
            # If there is already a network in the canvas, it is asked to the
            # user if continuing with opening.
            confirm_dialog = ConfirmDialog("Open network",
                                           "A new network will be opened "
                                           "cancelling the current nodes.\n"
                                           "Do you wish to continue?")
            confirm_dialog.exec()
            # If the user clicks on "yes", the canvas is cleaned, a net is
            # opened and the window title is updated.
            if confirm_dialog is not None:
                if confirm_dialog.confirm:
                    # The canvas is cleaned
                    self.canvas.clear_scene()
                    self.canvas.scene.has_changed_mode.connect(lambda: self.update_status())
                    self.canvas.scene.selectionChanged.connect(lambda: self.update_status())
                    self.update_status()
                    # A file is opened
                    self.canvas.project.open()
                    if self.canvas.project.network is not None:
                        self.setWindowTitle(self.SYSNAME + " - " + self.canvas.project.network.identifier)
        else:
            # If the canvas was already empty, the opening function is directly
            # called
            self.canvas.project.open()
            if self.canvas.project.network is not None:
                self.setWindowTitle(self.SYSNAME + " - " + self.canvas.project.network.identifier)

    def save(self, _as: bool = True):
        """
        This method saves the current network if the format is correct

        Parameters
        ----------
        _as : bool, optional
            This attribute distinguishes between "save" and "save as".
            If _as is True the network will be saved in a new file, while
            if _as is False the network will overwrite the current one.
            (Default: True)

        """

        if len(self.canvas.renderer.NN.nodes) == 0 or \
                len(self.canvas.renderer.NN.edges) == 0:
            # Limit case: one disconnected node -> new network with one node
            if len(self.canvas.renderer.disconnected_network) == 1:
                for node in self.canvas.renderer.disconnected_network:
                    try:
                        self.canvas.renderer.add_node_to_nn(node)
                        self.canvas.project.save(_as)
                        self.setWindowTitle(self.SYSNAME + " - " + self.canvas.project.network.identifier)
                    except Exception as e:
                        error_dialog = MessageDialog(str(e), MessageType.ERROR)
                        error_dialog.exec()

            # More than one disconnected nodes cannot be saved
            elif len(self.canvas.renderer.disconnected_network) > 1:
                not_sequential_dialog = MessageDialog("The network is not sequential, and "
                                                      "cannot be saved.",
                                                      MessageType.ERROR)
                not_sequential_dialog.exec()
            else:
                # Network is empty
                message = MessageDialog("The network is empty!", MessageType.MESSAGE)
                message.exec()

        elif self.canvas.renderer.is_nn_sequential():
            # If there are logical nodes, the network is sequential
            every_node_connected = True
            # every node has to be in the nodes dictionary
            for node in self.canvas.renderer.disconnected_network:
                if node not in self.canvas.project.network.nodes:
                    every_node_connected = False
                    break

            if every_node_connected:
                self.canvas.project.save(_as)
                if self.canvas.project.network is not None:
                    self.setWindowTitle(self.SYSNAME + " - " + self.canvas.project.network.identifier)
            else:
                # If there are disconnected nodes, a message is displayed to the
                # user to choose if saving only the connected network
                confirm_dialog = ConfirmDialog("Save network",
                                               "All the nodes outside the "
                                               "sequential network will lost.\n"
                                               "Do you wish to continue?")
                confirm_dialog.exec()
                if confirm_dialog.confirm:
                    self.canvas.project.save(_as)
                    if self.canvas.project.network is not None:
                        self.setWindowTitle(self.SYSNAME + " - " + self.canvas.project.network.identifier)
        else:
            # If the network is not sequential, it cannot be saved.
            not_sequential_dialog = MessageDialog("The network is not sequential and "
                                                  "cannot be saved.",
                                                  MessageType.ERROR)
            not_sequential_dialog.exec()

    def edit_action_validation(self) -> Optional[NodeBlock]:
        """
        This method performs a check on the object on which the edit
        action is called, in order to prevent unwanted operations.

        Returns
        ----------
        NodeBlock
            The graphic wrapper of the NetworkNode selected, if present.

        """

        if self.canvas.scene.selectedItems():
            if type(self.canvas.scene.selectedItems()[0]) is QGraphicsRectItem:
                # Return block graphic object
                return self.canvas.scene.blocks[self.canvas.scene.selectedItems()[0]]
            elif type(self.canvas.scene.selectedItems()[0]) is GraphicLine:
                msg_dialog = MessageDialog("Can't edit edges, please select a block instead.",
                                           MessageType.ERROR)
                msg_dialog.exec()
        else:
            err_dialog = MessageDialog("No block selected.", MessageType.MESSAGE)
            err_dialog.exec()

    def parameters_action_validation(self) -> Optional[NodeBlock]:
        """
        This method performs a check on the object on which the parameters
        action is called, in order to prevent unwanted operations.

        Returns
        ----------
        NodeBlock
            The graphic wrapper of the NetworkNode selected, if present.

        """

        if self.canvas.scene.selectedItems():
            if type(self.canvas.scene.selectedItems()[0]) is QGraphicsRectItem:
                # Return block graphic object
                return self.canvas.scene.blocks[self.canvas.scene.selectedItems()[0]]
            elif type(self.canvas.scene.selectedItems()[0]) is GraphicLine:
                msg_dialog = MessageDialog("No parameters available for connections.", MessageType.ERROR)
                msg_dialog.exec()
        else:
            err_dialog = MessageDialog("No block selected.", MessageType.MESSAGE)
            err_dialog.exec()

    @staticmethod
    def show_help():
        help_dialog = HelpDialog()
        help_dialog.exec()

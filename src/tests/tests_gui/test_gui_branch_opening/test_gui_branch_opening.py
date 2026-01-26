# Purpose of this file:
#  test the branch opening mechanism offered by the GUI
# 
# To execute the test:
# python -m pytest test_gui_branch_opening/test_gui_branch_opening.py

from never2.main_window import MainWindow
import pytest
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtCore import QPointF
from PyQt6 import QtWidgets
from PyQt6.QtWidgets import QMenu, QPushButton, QTreeWidget, QMessageBox
from collections import Counter

SEQUENCES_DIR = os.path.join(os.path.dirname(__file__), "sequences")
SEQUENCES_FILE = os.path.join(SEQUENCES_DIR, "branching_sequences.py")

# ---------- Helper: collect action sequences inside a file ----------
def load_sequences_from_file(file_path: str):
    import importlib.util

    spec = importlib.util.spec_from_file_location("seq_module", file_path)
    seq_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(seq_module)
    
    if hasattr(seq_module, "BRANCHING_SEQUENCES"):
        return seq_module.BRANCHING_SEQUENCES
    return []

# ---------- Collect all action sequences ----------
BRANCHING_SEQUENCES = load_sequences_from_file(SEQUENCES_FILE)

# ---------- Helper: compute clickable position of a block  ----------
def get_block_clickable_pos(graphics_block, graphics_view):
    rect = graphics_block.boundingRect() 
    offset = QPointF(-5, 5) # offset to not pick the border
    top_right_local = rect.topRight()
    click_local = top_right_local + offset
    top_right_scene = graphics_block.mapToScene(click_local)
    top_right_viewport = graphics_view.mapFromScene(top_right_scene)
    return top_right_viewport

# ---------- Helper: select multiple blocks in a QGraphicsView by simulating user clicks.  ----------
def select_gui_blocks(qtbot, graphics_view, graphics_scene, scene, selected_blocks):
    if not selected_blocks:
        return

    # get click positions
    click_positions = [get_block_clickable_pos(block.graphics_block, graphics_view) for block in selected_blocks]

    # Click first block (no Ctrl → resets selection)
    qtbot.mouseClick(
        graphics_view.viewport(),
        Qt.MouseButton.LeftButton,
        pos=click_positions[0]
    )

    # Click remaining blocks with Ctrl modifier
    for pos in click_positions[1:]:
        with qtbot.waitSignal(graphics_scene.selectionChanged):
            qtbot.mouseClick(
                graphics_view.viewport(),
                Qt.MouseButton.LeftButton,
                modifier=Qt.KeyboardModifier.ControlModifier,
                pos=pos
            )

# ---------- Helper: trigger a QAction from a QMainWindow menu by menu and action names   ----------
def trigger_menu_action(window, menu_name: str, action_name: str):
    # Traverse all menus in the menu bar
    for menu in window.menu_bar.findChildren(QMenu):
        if menu.title().replace("&", "") == menu_name:
            for action in menu.actions():
                if action.text() == action_name:
                    action.trigger()
                    return
    # If we get here, menu/action was not found
    raise ValueError(f"Action '{action_name}' not found in menu '{menu_name}'")

# ---------- Helper: find a QPushButton in a QTreeWidget by its top-level category and button text.   ----------
def get_button_by_category_and_name(toolbar_tree, category_name: str, button_name: str) -> QPushButton | None:
    # Iterate top-level items
    for i in range(toolbar_tree.topLevelItemCount()):
        top_item = toolbar_tree.topLevelItem(i)
        if top_item.text(0) == category_name:
            # Iterate child items
            for j in range(top_item.childCount()):
                child_item = top_item.child(j)
                button = toolbar_tree.itemWidget(child_item, 0)
                if isinstance(button, QPushButton) and button.text() == button_name:
                    return button
    return None

# ---------- Helper: simulate a click over a button in the layer toolbar  ----------
def select_toolbar_layer(qtbot, scene, toolbar_tree, gui_blocks_dict, category_name: str, layer_to_add: str):

    prev_num_blocks = len(scene.blocks)

    # Get the button inside the QTreeWidgetItem
    button = get_button_by_category_and_name(toolbar_tree, category_name, layer_to_add)

    # Simulate a click and wait for connected slot (if needed)
    with qtbot.waitSignal(button.clicked):
       qtbot.mouseClick(button, Qt.MouseButton.LeftButton)
    
    # if the inserction was successful
    if len(scene.blocks) == prev_num_blocks + 1:
      new_block_key = next(reversed(scene.blocks))
      new_block_idx = len(scene.blocks) - 1
      layer_string = layer_to_add + ' ' + str(new_block_idx)
      gui_blocks_dict[layer_string] = new_block_key

# The actual test
@pytest.mark.parametrize("sequence", BRANCHING_SEQUENCES)
def test_gui_branch_opening(qtbot, sequence):
    # launch the window
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    gui_blocks_dict = {}

    # get references
    toolbar_tree = window.editor_widget.layers_toolbar
    scene = window.editor_widget.scene
    graphics_scene = window.editor_widget.scene.graphics_scene
    graphics_view = window.editor_widget.scene.view 
    project = window.editor_widget.scene.project

    # add input/ouput
    gui_blocks_dict['Input 0'] = scene.input_block.id
    gui_blocks_dict['Output 1'] = scene.output_block.id

    # execute the sequence of actions (selection + addition)
    for action in sequence["actions"]:

        selected_items = action["selected_items"]
        layer_to_add = action["layer_to_add"]
        category_name = layer_to_add["category_name"]
        layer_name = layer_to_add["layer_name"]

        # Map selected_items to actual graphics blocks
        selected_blocks_ids = [gui_blocks_dict[item] for item in selected_items]
        selected_blocks = [scene.blocks[block_id] for block_id in selected_blocks_ids]

        # Select the items in the GUI
        select_gui_blocks(qtbot, graphics_view, graphics_scene, scene, selected_blocks)

        # Click the toolbar to add the new layer
        select_toolbar_layer(qtbot, scene, toolbar_tree, gui_blocks_dict, category_name, layer_name)

    # Branch opening test
    branching_layer = sequence["branching_layer"]

    branching_block = scene.blocks[gui_blocks_dict[branching_layer]]

    edges = [socket.edge for socket in branching_block.output_sockets]
    child_blocks = [edge.end_skt.block_ref._id for edge in edges]

    assert len(project.get_children_ids_by_id(branching_block._id)) > 1, (f"{branching_layer_name} is expected to branch, "
        f"but has only {len(children_ids)} child")
    assert len(branching_block.output_sockets) > 1
    assert all(socket.edge is not None for socket in branching_block.output_sockets)
    assert Counter(child_blocks) == Counter(project.get_children_ids_by_id(branching_block._id))

    # delete all blocks
    displayed_blocks = [
        block for block in scene.blocks.values()
        if block != scene.input_block and block != scene.output_block
    ]

    select_gui_blocks(qtbot, graphics_view, graphics_scene, scene, displayed_blocks)

    trigger_menu_action(window, "Edit", "Delete block")
    


import pytest

sequence_1 = {
  "branching_layer": "Fully Connected 2",
  "actions": [
    {
      "selected_items": ["Input 0"],
      "layer_to_add": {
        "category_name": "Linear layers",
        "layer_name": "Fully Connected"
      }
    },
    {
      "selected_items": ["Fully Connected 2"],
      "layer_to_add": {
        "category_name": "Activation layers",
        "layer_name": "ReLU"
      }
    },
    {
      "selected_items": ["ReLU 3"],
      "layer_to_add": {
        "category_name": "Dropout layers",
        "layer_name": "Dropout"
      }
    },
    {
      "selected_items": ["Dropout 4"],
      "layer_to_add": {
        "category_name": "Linear layers",
        "layer_name": "Fully Connected"
      }
    },
    {
      "selected_items": ["Fully Connected 5"],
      "layer_to_add": {
        "category_name": "Activation layers",
        "layer_name": "Tanh"
      }
    },
    {
      "selected_items": ["Fully Connected 2"],
      "layer_to_add": {
        "category_name": "Linear layers",
        "layer_name": "Fully Connected"
      }
    }
  ]
}
sequence_2 = {
  "branching_layer": "ReLU 3",
  "actions": [
    {
      "selected_items": ["Input 0"],
      "layer_to_add": {
        "category_name": "Linear layers",
        "layer_name": "Fully Connected"
      }
    },
    {
      "selected_items": ["Fully Connected 2"],
      "layer_to_add": {
        "category_name": "Activation layers",
        "layer_name": "ReLU"
      }
    },
    {
      "selected_items": ["ReLU 3"],
      "layer_to_add": {
        "category_name": "Dropout layers",
        "layer_name": "Dropout"
      }
    },
    {
      "selected_items": ["ReLU 3"],
      "layer_to_add": {
        "category_name": "Activation layers",
        "layer_name": "Tanh"
      }
    }
  ]
}

sequence_3 = {
  "branching_layer": "Fully Connected 4",
  "actions": [
    {
      "selected_items": ["Input 0"],
      "layer_to_add": {
        "category_name": "Linear layers",
        "layer_name": "Fully Connected"
      }
    },
    {
      "selected_items": ["Fully Connected 2"],
      "layer_to_add": {
        "category_name": "Activation layers",
        "layer_name": "ReLU"
      }
    },
    {
      "selected_items": ["ReLU 3"],
      "layer_to_add": {
        "category_name": "Linear layers",
        "layer_name": "Fully Connected"
      }
    },
    {
      "selected_items": ["Fully Connected 4"],
      "layer_to_add": {
        "category_name": "Activation layers",
        "layer_name": "Sigmoid"
      }
    },
    {
      "selected_items": ["Fully Connected 4"],
      "layer_to_add": {
        "category_name": "Dropout layers",
        "layer_name": "Dropout"
      }
    }
  ]
}

sequence_4 = {
  "branching_layer": "Fully Connected 2",
  "actions": [
    {
      "selected_items": ["Input 0"],
      "layer_to_add": {
        "category_name": "Linear layers",
        "layer_name": "Fully Connected"
      }
    },
    {
      "selected_items": ["Fully Connected 2"],
      "layer_to_add": {
        "category_name": "Activation layers",
        "layer_name": "ReLU"
      }
    },
    {
      "selected_items": ["Fully Connected 2"],
      "layer_to_add": {
        "category_name": "Activation layers",
        "layer_name": "Tanh"
      }
    },
    {
      "selected_items": ["ReLU 3", "Tanh 4"],
      "layer_to_add": {
        "category_name": "Merge layers",
        "layer_name": "Concat"
      }
    }
  ]
}

sequence_5 = {
  "branching_layer": "Fully Connected 2",
  "actions": [
    {
      "selected_items": ["Input 0"],
      "layer_to_add": {
        "category_name": "Linear layers",
        "layer_name": "Fully Connected"
      }
    },
    {
      "selected_items": ["Fully Connected 2"],
      "layer_to_add": {
        "category_name": "Activation layers",
        "layer_name": "ReLU"
      }
    },
    {
      "selected_items": ["Fully Connected 2"],
      "layer_to_add": {
        "category_name": "Activation layers",
        "layer_name": "Sigmoid"
      }
    },
    {
      "selected_items": ["Fully Connected 2"],
      "layer_to_add": {
        "category_name": "Dropout layers",
        "layer_name": "Dropout"
      }
    }
  ]
}

BRANCHING_SEQUENCES = [
    pytest.param(sequence_1, id="branch_fc_2"),
    pytest.param(sequence_2, id="branch_relu"),
    pytest.param(sequence_3, id="branch_fc_4"),
    pytest.param(sequence_4, id="branch_and_concat"),
    pytest.param(sequence_5, id="multi_branch"),
]
import pytest

sequence_1 = [
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
    },
    {
        "selected_items": ["Fully Connected 7", "Tanh 6"],
        "layer_to_add": {
            "category_name": "Merge layers",
            "layer_name": "Concat"
        }
    }
]

sequence_2 = [
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
            "category_name": "Normalization layers",
            "layer_name": "Batch Normalization"
        }
    },
    {
        "selected_items": ["Batch Normalization 3"],
        "layer_to_add": {
            "category_name": "Activation layers",
            "layer_name": "ReLU"
        }
    },
    {
        "selected_items": ["ReLU 4"],
        "layer_to_add": {
            "category_name": "Dropout layers",
            "layer_name": "Dropout"
        }
    },
    {
        "selected_items": ["Dropout 5"],
        "layer_to_add": {
            "category_name": "Linear layers",
            "layer_name": "Fully Connected"
        }
    },
    {
        "selected_items": ["Fully Connected 6", "ReLU 4"],
        "layer_to_add": {
            "category_name": "Merge layers",
            "layer_name": "Sum"
        }
    }
]

sequence_3 = [
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
            "layer_name": "ELU"
        }
    },
    {
        "selected_items": ["ELU 3"],
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
            "layer_name": "Sigmoid"
        }
    },
    {
        "selected_items": ["Sigmoid 6", "ELU 3"],
        "layer_to_add": {
            "category_name": "Merge layers",
            "layer_name": "Concat"
        }
    }
]

sequence_4 = [
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
            "layer_name": "Leaky ReLU"
        }
    },
    {
        "selected_items": ["Leaky ReLU 3"],
        "layer_to_add": {
            "category_name": "Normalization layers",
            "layer_name": "Batch Normalization"
        }
    },
    {
        "selected_items": ["Batch Normalization 4"],
        "layer_to_add": {
            "category_name": "Dropout layers",
            "layer_name": "Dropout"
        }
    },
    {
        "selected_items": ["Dropout 5"],
        "layer_to_add": {
            "category_name": "Utility layers",
            "layer_name": "Flatten"
        }
    },
    {
        "selected_items": ["Flatten 6", "Leaky ReLU 3"],
        "layer_to_add": {
            "category_name": "Merge layers",
            "layer_name": "Sum"
        }
    }
]

sequence_5 = [
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
            "category_name": "Normalization layers",
            "layer_name": "Batch Normalization"
        }
    },
    {
        "selected_items": ["Batch Normalization 3"],
        "layer_to_add": {
            "category_name": "Activation layers",
            "layer_name": "CELU"
        }
    },
    {
        "selected_items": ["CELU 4"],
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
        "selected_items": ["Tanh 6", "CELU 4"],
        "layer_to_add": {
            "category_name": "Merge layers",
            "layer_name": "Concat"
        }
    }
]

NEGATIVE_SEQUENCES = [
    pytest.param(sequence_1, id="seq_1"),
    pytest.param(sequence_2, id="seq_2"),
    pytest.param(sequence_3, id="seq_3"),
    pytest.param(sequence_4, id="seq_4"),
    pytest.param(sequence_5, id="seq_5"),
]


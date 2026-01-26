import torch
import pynever.strategies.conversion.converters.pytorch_layers as pyt_l

class PytL_Tracer(torch.fx.Tracer):
    """
    Custom torch.fx Tracer that treats our pytorch_layers 
    (pynever.strategies.conversion.converters.pytorch_layers) as leaf modules. 

    By marking these modules as leaves, the tracer emits them as `call_module` 
    operations instead of tracing into their internals. This ensures they are 
    preserved as standalone modules in the exported FX graph, which simplifies 
    handling them during the import/conversion phase.
    """
    def is_leaf_module(self, m, module_qualified_name):
        
        # Treat our custom pytorch layers as leaf
        pyt_l_modules = [pyt_l.Linear, 
                         pyt_l.ReLU,
                         pyt_l.CELU,
                         pyt_l.ELU,
                         pyt_l.LeakyReLU, 
                         pyt_l.Tanh,
                         pyt_l.Sigmoid,
                         pyt_l.Softmax,
                         pyt_l.BatchNorm1d, 
                         pyt_l.BatchNorm2d, 
                         pyt_l.BatchNorm3d, 
                         pyt_l.Conv1d,
                         pyt_l.Conv2d, 
                         pyt_l.Conv3d,
                         pyt_l.MaxPool1d,
                         pyt_l.MaxPool2d, 
                         pyt_l.MaxPool3d,
                         pyt_l.AvgPool1d,
                         pyt_l.AvgPool2d,
                         pyt_l.AvgPool3d,
                         pyt_l.Dropout, 
                         pyt_l.Flatten, 
                         pyt_l.Reshape,
                         pyt_l.Unsqueeze,
                         pyt_l.LocalResponseNorm]

        if any(isinstance(m, pyt_l_module) for pyt_l_module in pyt_l_modules):
            return True
        
        return super().is_leaf_module(m, module_qualified_name)
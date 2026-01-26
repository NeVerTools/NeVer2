# Never2 ResNet
### University of Genoa
#### ResNet integration in NeVer2

This project is an extension of [NeVerTools](https://github.com/NeVerTools), which provides the foundation for the work here.

The aim is to design and integrate in the Never2 tool the representation and parsing of residual neural networks (ResNets).  
Residual neural networks are a class of neural networks where the output of a layer can be forwarded to multiple layers, extending the performances w.r.t. "standard" feed forward models. The tool already allows to design and import feed forward models in the ONNX and PyTorch file formats, but lacks an interface towards ResNet models.  

The objectives are:
<ol type="i">
  <li>to create a parser from/to ResNet ONNX and PyTorch models for their verification and,</li>
  <li>to extend the graphical interface designer to include the representation and construction of such models.</li>
</ol>

RBF Features
===========

Introduction to RBF in py-dem-bones
---------------------------------

py-dem-bones integrates SciPy's Radial Basis Function (RBF) capabilities with Dem-Bones skeletal weight calculations to support advanced animation workflows. This integration enables:

1. Using Dem-Bones to calculate basic bone weights and transformations
2. Leveraging SciPy's RBFInterpolator to create parameter-driven auxiliary joints
3. Implementing functionality similar to Chad Vernon RBF nodes, but using standard Python scientific computing libraries

Key Advantages
-------------

* Uses production-grade SciPy implementation instead of custom RBF code
* Supports multiple RBF kernel function options (thin plate spline, multiquadric, gaussian, etc.)
* Seamlessly integrates with the Python scientific computing ecosystem
* Maintained and updated by the scientific computing community

RBF Kernel Functions
------------------

The following kernel functions are available through SciPy's RBFInterpolator:

* **thin_plate_spline**: φ(r) = r²log(r), suitable for smooth interpolation with minimal curvature
* **multiquadric**: φ(r) = sqrt(1 + (εr)²), good for general-purpose interpolation
* **inverse_multiquadric**: φ(r) = 1/sqrt(1 + (εr)²), creates smoother interpolations
* **gaussian**: φ(r) = exp(-(εr)²), creates very smooth interpolations with local influence
* **linear**: φ(r) = r, simple linear interpolation between points
* **cubic**: φ(r) = r³, provides smooth interpolation with more local control
* **quintic**: φ(r) = r⁵, higher-order polynomial with smoother derivatives

Where r is the distance between points and ε is a shape parameter that controls the influence radius.

Example Usage
------------

Here's a basic example of using RBF interpolation with py-dem-bones:

.. literalinclude:: ../examples/rbf_demo.py
   :language: python
   :linenos:
   :caption: RBF Interpolation Example

Maya Integration
--------------

To use the RBF functionality in Maya:

1. Implement the MayaDCCInterface to handle Maya-specific data structures
2. Replace matplotlib visualizations with Maya nodes/views
3. Consider Maya's Python environment compatibility

.. code-block:: python
   :caption: Maya RBF Integration Example (Simplified)

   import maya.cmds as cmds
   from py_dem_bones.interfaces.dcc import DCCInterface
   from scipy.interpolate import RBFInterpolator
   import numpy as np

   class MayaDCCInterface(DCCInterface):
       def from_dcc_data(self, **kwargs):
           # Implementation for Maya data extraction
           pass

       def to_dcc_data(self, **kwargs):
           # Implementation for Maya data application
           pass

   # Create RBF setup between two poses
   def create_rbf_setup(source_joint, target_joint, poses):
       # Extract pose data
       source_poses = []
       target_poses = []
       
       for pose in poses:
           # Set the pose
           cmds.setAttr(f"{pose['control']}.{pose['attribute']}", pose['value'])
           
           # Get joint positions
           source_pos = cmds.xform(source_joint, q=True, ws=True, t=True)
           target_pos = cmds.xform(target_joint, q=True, ws=True, t=True)
           
           source_poses.append([pose['value']])
           target_poses.append(target_pos)
       
       # Create RBF interpolator
       rbf = RBFInterpolator(
           np.array(source_poses),
           np.array(target_poses),
           kernel='thin_plate_spline'
       )
       
       return rbf

Jupyter Notebook Integration
-------------------------

A Jupyter Notebook version of the RBF demo is available for interactive exploration. The notebook includes:

* Interactive visualizations
* Step-by-step explanations with markdown
* Compatibility with Google Colab
* Installation instructions for dependencies

Compatibility
-----------

The RBF functionality requires:

* Python 3.7+
* SciPy 1.7.0+
* NumPy 1.20.0+

For Maya integration, compatibility has been tested with:

* Maya 2020+
* Python 3.7+ (as provided by Maya)

API Reference
-----------

For detailed API documentation, see the :doc:`Python API <python_api>` section.

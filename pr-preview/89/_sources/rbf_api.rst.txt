RBF API Reference
=================

This page provides detailed documentation for the RBF (Radial Basis Function) integration with py-dem-bones. This functionality enables advanced animation workflows by combining DemBones skeletal weight calculations with SciPy's RBF interpolation capabilities.

RBF Integration Overview
-----------------------

The integration between py-dem-bones and SciPy's RBF functionality allows for:

1. Using DemBones to calculate basic bone weights and transformations
2. Leveraging SciPy's RBFInterpolator to create parameter-driven auxiliary joints
3. Implementing functionality similar to Chad Vernon RBF nodes, but using standard Python scientific computing libraries

RBF Utility Functions
-------------------

.. py:function:: create_rbf_interpolator(key_poses, key_values, rbf_function='thin_plate_spline')

   Creates an RBF interpolator similar to Chad Vernon's RBF nodes.
   
   :param key_poses: Input values for key poses (n_samples, n_features)
   :param key_values: Output values for each key pose (n_samples, m)
   :param rbf_function: RBF function type, options include:
                        - 'thin_plate_spline': Thin plate spline (default)
                        - 'multiquadric': Multiquadric
                        - 'inverse_multiquadric': Inverse multiquadric
                        - 'gaussian': Gaussian function
                        - 'linear': Linear function
                        - 'cubic': Cubic function
                        - 'quintic': Quintic function
   :type key_poses: numpy.ndarray
   :type key_values: numpy.ndarray
   :type rbf_function: str
   :return: RBF interpolator object
   :rtype: scipy.interpolate.RBFInterpolator

RBF Kernel Functions
------------------

The following kernel functions are available through SciPy's RBFInterpolator:

* **thin_plate_spline**: φ(r) = r²log(r)
  
  Suitable for smooth interpolation with minimal curvature. This is the default kernel and works well for most animation scenarios.

* **multiquadric**: φ(r) = sqrt(1 + (εr)²)
  
  Good for general-purpose interpolation. The shape parameter ε controls the steepness of the interpolation.

* **inverse_multiquadric**: φ(r) = 1/sqrt(1 + (εr)²)
  
  Creates smoother interpolations than multiquadric. Useful when you want more gradual transitions.

* **gaussian**: φ(r) = exp(-(εr)²)
  
  Creates very smooth interpolations with local influence. The shape parameter ε controls the width of the Gaussian bell.

* **linear**: φ(r) = r
  
  Simple linear interpolation between points. Useful when you want direct linear blending between poses.

* **cubic**: φ(r) = r³
  
  Provides smooth interpolation with more local control than thin plate spline.

* **quintic**: φ(r) = r⁵
  
  Higher-order polynomial with smoother derivatives. Useful for very smooth transitions.

Where r is the distance between points and ε is a shape parameter that controls the influence radius.

Usage with DemBones
-----------------

The typical workflow for using RBF functionality with DemBones involves:

1. **Calculate bone weights and transformations** using DemBones:

   .. code-block:: python

      import py_dem_bones as pdb
      import numpy as np

      # Create DemBones instance
      dem_bones = pdb.DemBones()
      
      # Set parameters
      dem_bones.nIters = 30
      dem_bones.nnz = 4  # Number of non-zero weights per vertex
      
      # Set data
      dem_bones.nV = len(rest_pose)  # Number of vertices
      dem_bones.nB = num_bones  # Number of bones
      dem_bones.nF = 1  # Number of frames
      dem_bones.nS = 1  # Number of subjects
      dem_bones.u = rest_pose  # Rest pose
      dem_bones.v = deformed_pose  # Deformed pose
      
      # Compute skinning decomposition
      dem_bones.compute()
      
      # Get results
      weights = dem_bones.get_weights()
      transformations = dem_bones.get_transformations()

2. **Create RBF interpolator** for auxiliary joints:

   .. code-block:: python

      from scipy.interpolate import RBFInterpolator
      
      # Define key poses and corresponding joint positions
      key_poses = np.array([
          [0.0, 0.0],  # Default pose
          [1.0, 0.0],  # X-axis extreme
          [0.0, 1.0],  # Y-axis extreme
      ])
      
      # Define output values - auxiliary joint positions
      key_values = np.array([
          # Joint positions for default pose
          [[0.5, 0.5, 0.0], [0.5, 0.5, 1.0]],
          # Joint positions for X-axis extreme
          [[0.7, 0.5, 0.0], [0.7, 0.5, 1.2]],
          # Joint positions for Y-axis extreme
          [[0.5, 0.7, 0.0], [0.5, 0.7, 1.2]],
      ])
      
      # Create RBF interpolator
      rbf = RBFInterpolator(
          key_poses, 
          key_values.reshape(3, -1),
          kernel='thin_plate_spline',
          smoothing=0.0  # No smoothing, exact interpolation
      )

3. **Use the interpolator** to drive auxiliary joints:

   .. code-block:: python

      # Test pose
      test_pose = np.array([[0.5, 0.5]])
      
      # Get interpolated joint positions
      interpolated_positions = rbf(test_pose).reshape(-1, 3)

Integration with DCC Software
---------------------------

To use this functionality in Digital Content Creation (DCC) software like Maya, Blender, or Houdini, you'll need to:

1. Implement the appropriate DCCInterface for your software
2. Convert between the DCC's data structures and NumPy arrays
3. Apply the interpolated values to the appropriate controls or joints

For specific examples, see the :doc:`Maya RBF Example <../examples/maya_rbf_demo.py>` and :doc:`Blender RBF Example <../examples/blender_rbf_example.py>`.

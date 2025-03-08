.. py-dem-bones documentation master file

Welcome to py-dem-bones's documentation!
=======================================

**py-dem-bones** is a Python binding for the Dem Bones library, which provides an automated algorithm to extract the Linear Blend Skinning (LBS) with bone transformations from a set of example meshes.

Features
--------

* Python bindings for the Dem Bones C++ library
* Support for Python 3.7+
* Pythonic wrapper classes for easier integration
* Comprehensive error handling
* Cross-platform support (Windows, macOS, Linux)
* Pre-built wheels for common platforms
* Efficient conversion between NumPy arrays and Eigen matrices
* Integration with SciPy's RBF functionality for advanced animation workflows

.. toctree::
   :maxdepth: 1
   :caption: User Guide

   installation
   usage
   examples
   rbf_features

.. toctree::
   :maxdepth: 1
   :caption: API Reference

   api
   python_api
   rbf_api

.. toctree::
   :maxdepth: 1
   :caption: Development

   contributing
   ci_cd
   changelog

Quick Start
-----------

Installation
^^^^^^^^^^^^

.. code-block:: bash

   pip install py-dem-bones

Basic Usage
^^^^^^^^^^

.. code-block:: python

   import numpy as np
   import py_dem_bones as pdb

   # Create a DemBonesWrapper instance
   dem_bones = pdb.DemBonesWrapper()

   # Set parameters
   dem_bones.num_iterations = 30
   dem_bones.num_init_iterations = 10
   dem_bones.num_transform_iterations = 5
   dem_bones.num_weights_iterations = 3
   dem_bones.max_nonzeros_per_vertex = 4
   dem_bones.weights_smoothness = 1e-4

   # Set up data
   # ...

   # Compute skinning decomposition
   dem_bones.compute()

   # Get results
   weights = dem_bones.get_weights()
   transformations = dem_bones.get_transformations()

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

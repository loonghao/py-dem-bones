.. py-dem-bones documentation master file

Welcome to py-dem-bones's documentation!
==========================================

**py-dem-bones** binds the Dem Bones native solver and provides a host-independent NumPy contract for turning ordered mesh poses into linear blend skinning weights and bone transformations.

Features
--------

* Python bindings for the Dem Bones C++ library
* Support for Python 3.8+
* Host-independent mesh sequence API for DCC adapters
* Comprehensive error handling
* Cross-platform support (Windows, macOS, Linux)
* Pre-built wheels for common platforms
* Efficient conversion between NumPy arrays and Eigen matrices
* Complete transform output for every frame and bone

.. toctree::
   :maxdepth: 1
   :caption: User Guide

   installation
   usage
   dcc_integration
   showcase
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
   README
   ci_cd
   cibuildwheel
   adr/0001-validated-skinning-boundary
   adr/0002-host-adapters-and-native-kernel
   changelog

Quick Start
-----------

Installation
^^^^^^^^^^^^

.. code-block:: bash

   pip install py-dem-bones

Basic Usage
^^^^^^^^^^^

.. code-block:: python

   import numpy as np
   import py_dem_bones as pdb

   rest = np.array([[0., 0., 0.], [1., 0., 0.], [0., 1., 0.], [0., 0., 1.]])
   poses = np.stack([rest, rest + [0., 0., 0.2]])
   result = pdb.solve_skinning(rest, poses, bone_count=1)
   print(result.weights.shape, result.transforms.shape)

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

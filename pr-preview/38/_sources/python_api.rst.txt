Python API Reference
===================

.. note::
   This documentation is generated from the Python API and its type stubs. 
   Type stubs are automatically generated during the build process and are included in the package distribution.

This page provides detailed documentation for the Python API of the py-dem-bones package. For a high-level overview of the API, see the :doc:`API Reference <api>` page.

.. currentmodule:: py_dem_bones

Core Classes
-------------

.. autoclass:: DemBones
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__
   :inherited-members:

.. autoclass:: DemBonesExt
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__
   :inherited-members:

Wrapper Classes
----------------

.. autoclass:: DemBonesWrapper
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__
   :inherited-members:

.. autoclass:: DemBonesExtWrapper
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__
   :inherited-members:

Exception Classes
-----------------

.. autoclass:: DemBonesError
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: ParameterError
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: ComputationError
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: IndexError
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: NameError
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: ConfigurationError
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: NotImplementedError
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: IOError
   :members:
   :undoc-members:
   :show-inheritance:

Utility Functions
-----------------

.. autofunction:: numpy_to_eigen

.. autofunction:: eigen_to_numpy

Type Annotations
---------------

The package provides type annotations for all public APIs, which can be used with static type checkers like mypy or pyright.

Example:

.. code-block:: python

   from py_dem_bones import DemBonesWrapper
   import numpy as np
   
   # Type checkers will recognize these types
   bones = DemBonesWrapper()
   vertices = np.random.rand(10, 3)  # 10 vertices, 3 coordinates each
   weights = bones.compute(vertices)

Interfaces
----------

.. autoclass:: DCCInterface
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

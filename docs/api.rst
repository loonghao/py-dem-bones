API Reference
=============

This page provides an overview of the py-dem-bones API. For detailed Python API documentation, see the :doc:`Python API Reference <python_api>` page.

Python API Overview
------------------

Core Classes
~~~~~~~~~~~~

The core classes provide direct bindings to the C++ implementation:

- **DemBones**: The main class for skinning decomposition
- **DemBonesExt**: Extended version with support for hierarchical skeletons

Wrapper Classes
~~~~~~~~~~~~~~~

The wrapper classes provide a more Pythonic interface to the core functionality:

- **DemBonesWrapper**: Python-friendly wrapper for DemBones
- **DemBonesExtWrapper**: Python-friendly wrapper for DemBonesExt

Exception Classes
~~~~~~~~~~~~~~~~~

The exception classes provide structured error handling:

- **DemBonesError**: Base class for all py-dem-bones exceptions
- **ParameterError**: Raised for invalid parameter values
- **ComputationError**: Raised when computation fails
- **IndexError**: Raised for invalid indices
- **NameError**: Raised for name-related errors
- **ConfigurationError**: Raised for configuration errors
- **NotImplementedError**: Raised for unimplemented features
- **IOError**: Raised for input/output errors

Utility Functions
~~~~~~~~~~~~~~~~~

The utility functions provide helper functionality:

- **numpy_to_eigen**: Convert a NumPy array to an Eigen-compatible format
- **eigen_to_numpy**: Convert an Eigen matrix to a NumPy array

Interfaces
~~~~~~~~~~

The interfaces provide integration with external software:

- **DCCInterface**: Abstract base class for DCC software integration

C++ API
-------

The C++ API is the foundation of py-dem-bones and includes the following main components:

- **DemBones**: The core class for skinning decomposition
- **DemBonesExt**: Extended version with support for hierarchical skeletons
- **Eigen Integration**: Utilities for working with Eigen matrices
- **Error Handling**: C++ exception classes and error codes

For more details on the C++ implementation, please refer to the `Dem Bones repository <https://github.com/electronicarts/dem-bones>`_.

Usage Examples
------------

Basic Usage
~~~~~~~~~~~

.. code-block:: python

   import numpy as np
   import py_dem_bones as pdb

   # Create a DemBonesWrapper instance
   dem_bones = pdb.DemBonesWrapper()

   # Set parameters
   dem_bones.num_iterations = 30
   dem_bones.num_init_iterations = 10
   dem_bones.max_influences = 4
   dem_bones.weight_smoothness = 1e-4

   # Set up data
   # ...

   # Compute skinning decomposition
   dem_bones.compute()

   # Get results
   weights = dem_bones.get_weights()
   transformations = dem_bones.get_transformations()

Advanced Usage
~~~~~~~~~~~~~~

For advanced usage examples, including hierarchical skeletons and custom constraints, see the :doc:`examples` page.

Examples
========

Portable skinning decomposition
-------------------------------

Run this example with a normal Python interpreter after installing the
package. It solves two independently moving mesh components with the native
solver and prints the result shapes and reconstruction error.

.. literalinclude:: ../examples/portable_example.py
   :language: python
   :linenos:

For a DCC integration, sample ``rest``, ``poses`` and ``faces`` through the host API,
then apply the returned arrays through its skinning API. See
:doc:`dcc_integration` for the required layout and coordinate conversion.

The repository also contains short host-specific scripts under
`examples/ <https://github.com/loonghao/py-dem-bones/tree/main/examples>`_.
They import the packaged ``py_dem_bones.adapters`` modules and use the same
validated solver boundary. Consult :doc:`dcc_integration` for the required
SDK capabilities and the distinction between weight writing and animation
baking. The Unreal example requires an explicit sampler/writer bridge.

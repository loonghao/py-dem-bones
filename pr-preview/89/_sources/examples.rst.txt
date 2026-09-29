Examples
========

Portable skinning decomposition
-------------------------------

Run this example with a normal Python interpreter after installing the
package. It exercises the actual native solver and prints the result shapes.

.. literalinclude:: ../examples/portable_example.py
   :language: python
   :linenos:

For a DCC integration, sample ``rest`` and ``poses`` through the host API,
then apply the returned arrays through its skinning API. See
:doc:`dcc_integration` for the required layout and coordinate conversion.

The repository also contains older host-specific scripts under
`examples/ <https://github.com/loonghao/py-dem-bones/tree/main/examples>`_.
They illustrate SDK calls and must run inside their matching host. Their
mesh and matrix conventions should be checked against the portable contract
before production use.

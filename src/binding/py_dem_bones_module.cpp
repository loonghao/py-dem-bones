#include <pybind11/pybind11.h>

namespace py = pybind11;

// Forward declarations
void init_dem_bones(py::module& m);
void init_dem_bones_ext(py::module& m);

PYBIND11_MODULE(_py_dem_bones, m) {
    m.doc() = "Python bindings for the Dem Bones library";
    
    // Initialize submodules
    init_dem_bones(m);
    init_dem_bones_ext(m);
    
    // Version information
    m.attr("__version__") = "0.1.0";
    m.attr("__dem_bones_version__") = "v1.2.1-2-g09b899b";
}

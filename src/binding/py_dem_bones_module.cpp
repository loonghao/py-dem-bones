#include <pybind11/pybind11.h>

namespace py = pybind11;

// Forward declarations
void init_dem_bones(py::module& m);
void init_dem_bones_ext(py::module& m);

PYBIND11_MODULE(_py_dem_bones, m) {
    m.doc() = "Python bindings for the Dem Bones library";

    // Add version information
    m.attr("__dem_bones_version__") = "1.2.1";

    // Initialize submodules
    init_dem_bones(m);
    init_dem_bones_ext(m);
}

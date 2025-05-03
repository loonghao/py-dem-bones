// pybind11 configuration
#define PYBIND11_COMPILER_TYPE ""
#define PYBIND11_STDLIB ""
#define PYBIND11_BUILD_ABI ""

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
}

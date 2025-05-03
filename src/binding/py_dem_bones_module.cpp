// Define Py_LIMITED_API before including any headers
// This is crucial for using Python Limited API (abi3)
#define Py_LIMITED_API 0x03090000  // Python 3.9 API

// pybind11 configuration
#define PYBIND11_COMPILER_TYPE ""
#define PYBIND11_STDLIB ""
#define PYBIND11_BUILD_ABI ""

// Use PYBIND11_USE_STABLE_ABI to enable abi3 support
#define PYBIND11_USE_STABLE_ABI 1

// Disable strict mode to allow access to more APIs
#define PYBIND11_STRICT_PYTHON_LIMITED_API 0

// Set pybind11 internals version to avoid ABI compatibility issues
#define PYBIND11_INTERNALS_VERSION "10.0.0"

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

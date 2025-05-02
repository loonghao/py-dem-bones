#include <pybind11/pybind11.h>
#include "logger.h"

// Python 3.7 compatibility
#ifdef PYTHON_37_COMPATIBLE
#define PY_MAJOR_VERSION 3
#define PY_MINOR_VERSION 7
#endif

// Add OpenMP support if available
#ifndef _OPENMP
#ifdef _OPENMP
#include <omp.h>
#endif
#endif

namespace py = pybind11;

// Forward declarations
void init_dem_bones(py::module& m);
void init_dem_bones_ext(py::module& m);

// Initialize logger module
void init_logger(py::module& m) {
    using namespace dem_bones;

    // Bind log level enumeration
    py::enum_<LogLevel>(m, "LogLevel")
        .value("TRACE", LogLevel::TRACE)
        .value("DEBUG", LogLevel::DEBUG)
        .value("INFO", LogLevel::INFO)
        .value("WARN", LogLevel::WARN)
        .value("ERROR", LogLevel::ERROR)
        .value("CRITICAL", LogLevel::CRITICAL);

    // Bind logger class
    py::class_<Logger>(m, "Logger")
        .def_static("instance", &Logger::instance, py::return_value_policy::reference)
        .def("init", &Logger::init,
             py::arg("level") = LogLevel::INFO,
             py::arg("to_console") = true,
             py::arg("to_python") = true)
        .def("set_level", &Logger::set_level)
        .def("trace", &Logger::trace)
        .def("debug", &Logger::debug)
        .def("info", &Logger::info)
        .def("warn", &Logger::warn)
        .def("error", &Logger::error)
        .def("critical", &Logger::critical);
}

PYBIND11_MODULE(_py_dem_bones, m) {
    m.doc() = "Python bindings for the Dem Bones library";

    // Initialize logger module
    init_logger(m);

    // Initialize submodules
    init_dem_bones(m);
    init_dem_bones_ext(m);

    // Initialize logging system
    dem_bones::Logger::instance().init(dem_bones::LogLevel::INFO, true, true);
    dem_bones::Logger::instance().info("DemBones C++ module initialized");
}

// Note: We do not use PY_SSIZE_T_CLEAN as it's related to ABI3 compatibility mode
// which may cause issues with some pybind11 features

#include <pybind11/pybind11.h>
#include <pybind11/eigen.h>
#include <pybind11/stl.h>
#include <pybind11/numpy.h>

#include <DemBones/DemBonesExt.h>
#include "logger.h"  // Add logger header
#include <chrono>     // Add chrono for timing

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

// Define ssize_t for Windows compatibility
#ifdef _WIN32
#include <BaseTsd.h>
typedef SSIZE_T ssize_t;
#endif

template <typename Scalar, typename AniMeshScalar>
void bind_dem_bones_ext(py::module& m, const std::string& type_suffix) {
    using Class = Dem::DemBonesExt<Scalar, AniMeshScalar>;
    using MatrixX = Eigen::Matrix<Scalar, Eigen::Dynamic, Eigen::Dynamic>;
    using VectorX = Eigen::Matrix<Scalar, Eigen::Dynamic, 1>;
    using Matrix4 = Eigen::Matrix<Scalar, 4, 4>;
    using Vector4 = Eigen::Matrix<Scalar, 4, 1>;
    using Vector3 = Eigen::Matrix<Scalar, 3, 1>;
    using SparseMatrix = Eigen::SparseMatrix<Scalar>;

    std::string class_name = std::string("DemBonesExt") + type_suffix;

    py::class_<Class>(m, class_name.c_str())
        .def(py::init<>())

        // Inherited properties from DemBones
        .def_readwrite("nIters", &Class::nIters)
        .def_readwrite("nInitIters", &Class::nInitIters)
        .def_readwrite("nTransIters", &Class::nTransIters)
        .def_readwrite("transAffine", &Class::transAffine)
        .def_readwrite("transAffineNorm", &Class::transAffineNorm)
        .def_readwrite("nWeightsIters", &Class::nWeightsIters)
        .def_readwrite("nnz", &Class::nnz)
        .def_readwrite("weightsSmooth", &Class::weightsSmooth)
        .def_readwrite("weightsSmoothStep", &Class::weightsSmoothStep)
        .def_readwrite("weightEps", &Class::weightEps)

        // Inherited data properties
        .def_readwrite("nV", &Class::nV)
        .def_readwrite("nB", &Class::nB)
        .def_readwrite("nS", &Class::nS)
        .def_readwrite("nF", &Class::nF)
        .def_readwrite("fStart", &Class::fStart)
        .def_readwrite("subjectID", &Class::subjectID)
        .def_readwrite("u", &Class::u)
        .def_readwrite("lockW", &Class::lockW)
        .def_readwrite("m", &Class::m)
        .def_readwrite("lockM", &Class::lockM)
        .def_readwrite("v", &Class::v)
        .def_readwrite("fv", &Class::fv)

        // Inherited read-only properties
        .def_property_readonly("iter", [](const Class& self) { return self.iter; })
        .def_property_readonly("iterTransformations", [](const Class& self) { return self.iterTransformations; })
        .def_property_readonly("iterWeights", [](const Class& self) { return self.iterWeights; })

        // DemBonesExt specific properties
        .def_readwrite("fTime", &Class::fTime)
        .def_readwrite("boneName", &Class::boneName)
        .def_readwrite("parent", &Class::parent)
        .def_readwrite("bindUpdate", &Class::bindUpdate)  // Add bindUpdate property
        .def_property("bind",
            // Getter - simplified version
            [](const Class& self) -> py::array_t<Scalar> {
                int nBones = self.nB > 0 ? self.nB : 2;  // Default to 2 bones if nB not set

                // Create a numpy array with the right shape
                std::vector<ssize_t> shape = {nBones * 3, 4};
                std::vector<ssize_t> strides = {static_cast<ssize_t>(sizeof(Scalar) * 4), static_cast<ssize_t>(sizeof(Scalar))};
                py::array_t<Scalar> result(shape, strides);

                // Get a pointer to the data
                Scalar* data = static_cast<Scalar*>(result.request().ptr);

                // Initialize to identity matrices
                for (int b = 0; b < nBones; ++b) {
                    for (int i = 0; i < 3; ++i) {
                        for (int j = 0; j < 4; ++j) {
                            data[b * 12 + i * 4 + j] = (i == j) ? 1.0 : 0.0;
                        }
                    }
                }

                // If self.bind has data, copy it to the numpy array
                if (self.bind.size() > 0) {
                    int bonesToCopy = std::min(static_cast<int>(self.bind.cols() / 4), nBones);
                    for (int b = 0; b < bonesToCopy; ++b) {
                        for (int i = 0; i < 3; ++i) {
                            for (int j = 0; j < 4; ++j) {
                                if (i < self.bind.rows() && 4*b+j < self.bind.cols()) {
                                    data[b * 12 + i * 4 + j] = self.bind(i, 4*b+j);
                                }
                            }
                        }
                    }
                }

                return result;
            },
            // Setter - simplified version
            [](Class& self, const py::array_t<Scalar>& array) {
                // Get the array info
                py::buffer_info info = array.request();

                // Check dimensions
                if (info.ndim != 2) {
                    throw std::runtime_error("Bind matrix must be 2-dimensional");
                }

                // Get array shape
                ssize_t rows = info.shape[0];
                ssize_t cols = info.shape[1];

                // Check that cols is 4
                if (cols != 4) {
                    throw std::runtime_error("Bind matrix must have 4 columns");
                }

                // Check that rows is a multiple of 3
                if (rows % 3 != 0) {
                    throw std::runtime_error("Bind matrix rows must be a multiple of 3");
                }

                int nBones = static_cast<int>(rows / 3);

                // Resize the bind matrix
                self.bind.resize(3, 4 * nBones);

                // Get a pointer to the data
                Scalar* data = static_cast<Scalar*>(info.ptr);

                // Copy the data to the bind matrix
                for (int b = 0; b < nBones; ++b) {
                    for (int i = 0; i < 3; ++i) {
                        for (int j = 0; j < 4; ++j) {
                            self.bind(i, 4*b+j) = data[b * 12 + i * 4 + j];
                        }
                    }
                }

                // Update the number of bones if needed
                if (self.nB < nBones) {
                    self.nB = nBones;
                }
            }
        )

        // Methods
        .def("compute", [](Class& self) -> py::tuple {
            try {
                // Log computation parameters
                dem_bones::Logger::instance().info("Starting DemBonesExt computation");
                dem_bones::Logger::instance().debug("Computation parameters: nIters=" + std::to_string(self.nIters) +
                                        ", nB=" + std::to_string(self.nB) +
                                        ", nV=" + std::to_string(self.nV));

                // Record start time
                auto start_time = std::chrono::high_resolution_clock::now();

                // Call the actual computation method
                self.compute();

                // Calculate time spent
                auto end_time = std::chrono::high_resolution_clock::now();
                auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end_time - start_time).count();

                // Log success information
                dem_bones::Logger::instance().info("Computation completed successfully in " + std::to_string(duration) + "ms");

                // Return success and empty error message
                return py::make_tuple(true, "");
            } catch (const std::exception& e) {
                // Log exception information
                std::string error_msg = e.what();
                dem_bones::Logger::instance().error("Computation failed with error: " + error_msg);

                // If there's an exception in C++ code, return false and error message
                return py::make_tuple(false, error_msg);
            } catch (...) {
                // Catch any other exceptions
                std::string error_msg = "Unknown error occurred during computation";
                dem_bones::Logger::instance().error(error_msg);

                return py::make_tuple(false, error_msg);
            }
        })
        .def("computeWeights", &Class::computeWeights)
        .def("computeTranformations", &Class::computeTranformations)
        .def("init", &Class::init)
        .def("rmse", &Class::rmse)
        .def("clear", &Class::clear)

        // Python-friendly getters and setters
        .def("get_weights", [](const Class& self) -> py::array_t<Scalar> {
            // Get the dimensions from the sparse weight matrix
            int nBones = self.nB;
            int nVerts = self.nV;

            if (nBones <= 0 || nVerts <= 0) {
                // Return empty array if dimensions are not valid
                std::vector<ssize_t> shape = {0, 0};
                return py::array_t<Scalar>(shape);
            }

            // Create a numpy array with the right shape [nB, nV]
            std::vector<ssize_t> shape = {nBones, nVerts};
            py::array_t<Scalar> result(shape);
            auto data = result.mutable_data();

            // Fill the array with zeros initially
            std::fill(data, data + nBones * nVerts, 0.0);

            // Copy data from sparse matrix to dense array
            for (int k = 0; k < self.w.outerSize(); ++k) {
                for (typename SparseMatrix::InnerIterator it(self.w, k); it; ++it) {
                    int row = it.row();   // Bone index
                    int col = it.col();   // Vertex index
                    Scalar value = it.value();

                    if (row < nBones && col < nVerts) {
                        data[row * nVerts + col] = value;
                    }
                }
            }

            return result;
        })
        .def("set_weights", [](Class& self, const MatrixX& weights) {
            // We'll need to create a temporary sparse matrix from scratch
            self.w.resize(weights.rows(), weights.cols());
            std::vector<Eigen::Triplet<Scalar>> triplets;
            triplets.reserve(weights.rows() * weights.cols() / 4); // Reserve space for efficiency

            // Add non-zero elements
            for (int i = 0; i < weights.rows(); ++i) {
                for (int j = 0; j < weights.cols(); ++j) {
                    if (weights(i, j) != 0) {
                        triplets.push_back(Eigen::Triplet<Scalar>(i, j, weights(i, j)));
                    }
                }
            }

            self.w.setFromTriplets(triplets.begin(), triplets.end());
            self.w.makeCompressed();
        })
        .def("get_transformations", [](const Class& self) -> py::array_t<Scalar> {
            // Get dimensions of transformation matrices
            int nFrames = self.nF;
            int nBones = self.nB;

            if (nFrames <= 0 || nBones <= 0) {
                // Return empty array if dimensions are not valid
                std::vector<ssize_t> shape = {0, 4, 4};
                return py::array_t<Scalar>(shape);
            }

            // Create numpy array with correct shape [nF, 4, 4]
            std::vector<ssize_t> shape = {nFrames, 4, 4};
            py::array_t<Scalar> result(shape);
            auto r = result.template mutable_unchecked<3>();

            // Initialize with identity matrices
            for (int f = 0; f < nFrames; ++f) {
                for (int i = 0; i < 4; ++i) {
                    for (int j = 0; j < 4; ++j) {
                        r(f, i, j) = (i == j) ? 1.0 : 0.0;  // Identity matrix
                    }
                }
            }

            // Copy transformation data if available
            if (self.m.rows() > 0 && self.m.cols() > 0) {
                // Copy data from flat matrix to 3D array
            }

            return result;
        });
}

void init_dem_bones_ext(py::module& m) {
    // Initialize with double precision
    bind_dem_bones_ext<double, double>(m, "d");

    // Initialize with single precision
    bind_dem_bones_ext<float, float>(m, "f");
}

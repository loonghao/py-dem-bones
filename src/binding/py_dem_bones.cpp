#include <pybind11/pybind11.h>
#include <pybind11/eigen.h>
#include <pybind11/stl.h>
#include <pybind11/numpy.h>

#include <DemBones/DemBones.h>

// Define ssize_t for Windows compatibility
#ifdef _WIN32
    #include <BaseTsd.h>
    // Use Py_ssize_t instead of redefining ssize_t which conflicts with Python's definition
    #ifndef Py_ssize_t
        #define Py_ssize_t SSIZE_T
    #endif
#endif

namespace py = pybind11;

template <typename Scalar, typename AniMeshScalar>
void bind_dem_bones(py::module& m, const std::string& type_suffix) {
    using Class = Dem::DemBones<Scalar, AniMeshScalar>;
    using MatrixX = Eigen::Matrix<Scalar, Eigen::Dynamic, Eigen::Dynamic>;
    using VectorX = Eigen::Matrix<Scalar, Eigen::Dynamic, 1>;
    using Matrix4 = Eigen::Matrix<Scalar, 4, 4>;
    using Vector4 = Eigen::Matrix<Scalar, 4, 1>;
    using Vector3 = Eigen::Matrix<Scalar, 3, 1>;
    using SparseMatrix = Eigen::SparseMatrix<Scalar>;

    std::string class_name = std::string("DemBones") + type_suffix;

    py::class_<Class>(m, class_name.c_str())
        .def(py::init<>())
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

        // Data properties
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

        // Read-only properties - using lambda for reference members
        .def_property_readonly("iter", [](const Class& self) { return self.iter; })
        .def_property_readonly("iterTransformations", [](const Class& self) { return self.iterTransformations; })
        .def_property_readonly("iterWeights", [](const Class& self) { return self.iterWeights; })


        // Methods - direct call to C++ methods
        .def("compute", &Class::compute)
        .def("computeWeights", &Class::computeWeights)
        .def("computeTranformations", &Class::computeTranformations)
        .def("init", &Class::init)
        .def("rmse", &Class::rmse)
        .def("clear", &Class::clear)

        // Python-friendly getters and setters - direct access to sparse matrix data
        .def("get_weights", [](const Class& self) -> py::array_t<Scalar> {
            // Get actual dimensions
            int nBones = self.nB;
            int nVerts = self.nV;

            // If dimensions are invalid, return empty array
            if (nBones <= 0 || nVerts <= 0) {
                // Create an empty array without using initializer list
                std::vector<py::ssize_t> shape = {0, 0};
                return py::array_t<Scalar>(shape);
            }

            // Create result array
            py::array_t<Scalar> result({nBones, nVerts});
            auto data = result.mutable_data();

            // Initialize to 0
            std::fill(data, data + nBones * nVerts, 0.0);

            // Copy non-zero elements from sparse matrix
            for (int j = 0; j < nVerts; ++j) {
                for (typename SparseMatrix::InnerIterator it(self.w, j); it; ++it) {
                    data[it.row() * nVerts + j] = it.value();
                }
            }

            return result;
        })
        .def("set_weights", [](Class& self, const MatrixX& weights) {
            // We'll need to create a temporary sparse matrix from scratch
            self.w.resize(weights.rows(), weights.cols());
            std::vector<Eigen::Triplet<Scalar>> triplets;

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
            // Get actual frame count
            int nFrames = self.nF;
            int nBones = self.nB;

            // If dimensions are invalid, return empty array
            if (nFrames <= 0 || nBones <= 0) {
                // Create an empty array without using initializer list
                std::vector<py::ssize_t> shape = {0, 4, 4};
                return py::array_t<Scalar>(shape);
            }

            // Create result array for the first bone's transformations
            // In a real application, you might want to return all bones' transformations
            py::array_t<Scalar> result({nFrames, 4, 4});
            auto r = result.template mutable_unchecked<3>();

            // Initialize to identity matrices
            for (int f = 0; f < nFrames; ++f) {
                for (int i = 0; i < 4; ++i) {
                    for (int j = 0; j < 4; ++j) {
                        r(f, i, j) = (i == j) ? 1.0 : 0.0;
                    }
                }
            }

            // If transformation data is available and has the expected dimensions
            if (self.m.rows() == nFrames * 4 && self.m.cols() == nBones * 4) {
                // Extract transformation for the first bone (bone 0)
                // In a real application, you might want to handle all bones
                for (int f = 0; f < nFrames; ++f) {
                    for (int i = 0; i < 4; ++i) {
                        for (int j = 0; j < 4; ++j) {
                            // Access the transformation matrix for frame f, bone 0
                            // The layout is [frame*4 + row, bone*4 + col]
                            r(f, i, j) = self.m(f * 4 + i, j);
                        }
                    }
                }
            }

            return result;
        })
        .def("set_transformations", [](Class& self, const MatrixX& transformations) {
            self.m = transformations;
        })
        .def("get_rest_pose", [](const Class& self) {
            return self.u;
        })
        .def("set_rest_pose", [](Class& self, const MatrixX& rest_pose) {
            self.u = rest_pose;
        })
        .def("get_animated_poses", [](const Class& self) {
            return self.v;
        })
        .def("set_animated_poses", [](Class& self, const MatrixX& animated_poses) {
            self.v = animated_poses;
        })

        // Documentation
        .doc() = "Smooth skinning decomposition with rigid bones and sparse, convex weights";
}

void init_dem_bones(py::module& m) {
    // Bind double precision version (most common)
    bind_dem_bones<double, double>(m, "");

    // Optionally bind single precision version
    bind_dem_bones<float, float>(m, "F");


}

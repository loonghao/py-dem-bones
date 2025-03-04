"""
Mock modules for sphinx-gallery to handle imports in examples.
"""
import sys
from unittest.mock import MagicMock


class MockDemBones:
    """Mock DemBones class for documentation."""
    
    def __init__(self):
        """Initialize DemBones."""
        self.nIters = 20
        self.nInitIters = 10
        self.nTransIters = 5
        self.nWeightsIters = 3
        self.nnz = 4
        self.weightsSmooth = 1e-4
        self.nV = 0
        self.nB = 0
        self.nF = 0
        self.nS = 0
        self.fStart = None
        self.subjectID = None
        self.u = None
        self.v = None
    
    def compute(self):
        """Compute skinning decomposition."""
        pass
    
    def get_weights(self):
        """Get skinning weights."""
        import numpy as np
        return np.zeros((self.nV, self.nB))
    
    def get_transformations(self):
        """Get bone transformations."""
        import numpy as np
        return np.zeros((self.nF, self.nB, 3, 4))


class MockModule(MagicMock):
    """Mock module for sphinx-gallery."""
    
    @classmethod
    def __getattr__(cls, name):
        if name == "DemBones":
            return MockDemBones
        return MagicMock()


# Add mock modules
MOCK_MODULES = ['py_dem_bones']
for mod_name in MOCK_MODULES:
    sys.modules[mod_name] = MockModule()

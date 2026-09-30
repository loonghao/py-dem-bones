"""RBF demo lifecycle checks without requiring a DCC or optional SciPy install."""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys
from types import ModuleType

import numpy as np
import pytest


def load_example(name):
    path = Path(__file__).parents[1] / "examples" / f"{name}.py"
    spec = spec_from_file_location(name, path)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def maya_rbf_demo(monkeypatch):
    events = []
    outcomes = {"import": True, "export": True}
    maya = ModuleType("maya")
    cmds = ModuleType("maya.cmds")
    cmds.objExists = lambda name: events.append(("scene", name)) or False
    maya.cmds = cmds
    monkeypatch.setitem(sys.modules, "maya", maya)
    monkeypatch.setitem(sys.modules, "maya.cmds", cmds)

    scipy = ModuleType("scipy")
    interpolate = ModuleType("scipy.interpolate")

    def interpolator(*args, **kwargs):
        events.append(("rbf",))
        return lambda values: np.zeros((len(values), 6))

    interpolate.RBFInterpolator = interpolator
    scipy.interpolate = interpolate
    monkeypatch.setitem(sys.modules, "scipy", scipy)
    monkeypatch.setitem(sys.modules, "scipy.interpolate", interpolate)

    adapter_module = ModuleType("py_dem_bones.adapters.maya")

    class Adapter:
        last_error = "invalid samples"

        def from_dcc_data(self, **kwargs):
            events.append(("import", kwargs))
            return outcomes["import"]

        def compute(self):
            events.append(("compute",))
            return True

        def to_dcc_data(self, **kwargs):
            events.append(("export", kwargs))
            return {"success": outcomes["export"], "error": "write refused"}

    adapter_module.MayaDCCInterface = Adapter
    monkeypatch.setitem(sys.modules, "py_dem_bones.adapters.maya", adapter_module)
    # A demo must not depend on sibling examples being installed as modules.
    monkeypatch.setitem(sys.modules, "maya_example", None)
    monkeypatch.setitem(sys.modules, "blender_example", None)
    module = load_example("maya_rbf_demo")
    monkeypatch.setattr(module, "create_cube_mesh", lambda: "cube")
    monkeypatch.setattr(module, "create_joints", lambda: ["left", "right"])
    monkeypatch.setattr(module, "create_rbf_joints", lambda: ["aux1", "aux2"])
    return module, events, outcomes


def test_maya_demo_requires_sampled_poses_before_scene_changes(maya_rbf_demo):
    module, events, _ = maya_rbf_demo
    assert module.main() is False
    assert events == []


def test_maya_demo_uses_adapter_lifecycle_and_reports_offline_preview(maya_rbf_demo, capsys):
    module, events, _ = maya_rbf_demo
    assert module.main(anim_mesh_names=["pose1", "pose2"]) is True
    lifecycle = [event for event in events if event[0] != "scene"]
    assert [event[0] for event in lifecycle] == ["import", "compute", "export", "rbf"]
    assert lifecycle[0][1]["anim_mesh_names"] == ["pose1", "pose2"]
    assert "Live RBF-driven joints are not implemented" in capsys.readouterr().out


@pytest.mark.parametrize("failure", ["import", "export"])
def test_maya_demo_stops_after_adapter_failure(maya_rbf_demo, failure):
    module, events, outcomes = maya_rbf_demo
    outcomes[failure] = False
    assert module.main(anim_mesh_names=["pose1", "pose2"]) is False
    lifecycle = [event[0] for event in events if event[0] != "scene"]
    assert lifecycle == (["import"] if failure == "import" else ["import", "compute", "export"])


def test_maya_live_rbf_setup_fails_explicitly_without_creating_nodes(maya_rbf_demo):
    module, events, _ = maya_rbf_demo
    with pytest.raises(NotImplementedError, match="Maya evaluation node or callback"):
        module.setup_rbf_driven_keys("control", "joint", object())
    assert events == []


def test_blender_rbf_has_no_sibling_adapter_dependency(maya_rbf_demo):
    module = load_example("blender_rbf_example")
    driver = module.BlenderRBFDriver()
    assert driver.is_initialized is False
    assert driver.poses == []

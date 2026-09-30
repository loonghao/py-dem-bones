"""Opt-in Maya standalone acceptance; run with mayapy, not regular pytest.

Example::

    mayapy tests/integration/maya_skinning_smoke.py --plugin dcc_mcp_maya_plugin.py

The caller supplies the DCC-MCP runtime environment and an installed wheel, or
an isolated wheel installation through ``--site-packages``. The final stdout
line is JSON; Maya and the plugin may also write diagnostic output. This checks
plugin loading and native solving inside Maya, not gateway tool dispatch.
"""

# Import standard library modules
import argparse
import json
from pathlib import Path
import sys


def _mesh_data(mesh, cmds, om, np):
    selection = om.MSelectionList()
    selection.add(cmds.listRelatives(mesh, shapes=True, fullPath=True)[0])
    mesh_fn = om.MFnMesh(selection.getDagPath(0))
    points = np.asarray([(p.x, p.y, p.z) for p in mesh_fn.getPoints(om.MSpace.kWorld)], dtype=np.float64)
    face_counts, vertex_ids = mesh_fn.getVertices()
    faces = []
    offset = 0
    for count in face_counts:
        faces.append(list(vertex_ids[offset:offset + count]))
        offset += count
    return points, faces


def _solve_case(bone_count, cmds, om, np, solve_skinning, tolerance):
    if bone_count == 1:
        mesh = cmds.polyCube(name="demBonesSmokeRigid", constructionHistory=False)[0]
    else:
        left = cmds.polyCube(name="demBonesSmokeLeft", constructionHistory=False)[0]
        right = cmds.polyCube(name="demBonesSmokeRight", constructionHistory=False)[0]
        cmds.move(-2, 0, 0, left, absolute=True, worldSpace=True)
        cmds.move(2, 0, 0, right, absolute=True, worldSpace=True)
        mesh = cmds.polyUnite(left, right, name="demBonesSmokePair", constructionHistory=False)[0]

    rest, faces = _mesh_data(mesh, cmds, om, np)
    poses = [rest]
    for step in (1, 2, 3):
        for index, point in enumerate(rest):
            displacement = [0, 0, step * 0.25]
            if bone_count == 2 and point[0] > 0:
                displacement = [0, step * 0.25, 0]
            cmds.xform(f"{mesh}.vtx[{index}]", worldSpace=True, translation=(point + displacement).tolist())
        pose, pose_faces = _mesh_data(mesh, cmds, om, np)
        if pose_faces != faces:
            raise RuntimeError("Maya mesh topology changed while sampling poses")
        poses.append(pose)
    poses = np.stack(poses)

    result = solve_skinning(rest, poses, bone_count=bone_count, faces=faces)
    if result.weights.shape != (bone_count, len(rest)):
        raise RuntimeError(f"Unexpected weight shape: {result.weights.shape}")
    if result.transforms.shape != (len(poses), bone_count, 4, 4):
        raise RuntimeError(f"Unexpected transform shape: {result.transforms.shape}")
    np.testing.assert_allclose(result.weights.sum(axis=0), 1, atol=1e-8)
    if np.any(result.weights < -1e-8):
        raise RuntimeError("Solver returned negative weights")
    transformed = (
        np.einsum("fbij,vj->fbvi", result.transforms[:, :, :3, :3], rest)
        + result.transforms[:, :, None, :3, 3]
    )
    reconstructed = np.einsum("bv,fbvi->fvi", result.weights, transformed)
    rmse = float(np.sqrt(np.mean((reconstructed - poses) ** 2)))
    if not np.isfinite(rmse) or rmse > tolerance:
        raise RuntimeError(f"{bone_count}-bone reconstruction RMSE {rmse} exceeds {tolerance}")
    return {"bones": bone_count, "vertices": len(rest), "faces": len(faces), "frames": len(poses), "rmse": rmse}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--plugin", required=True, help="DCC-MCP Maya plugin path or discoverable plugin name")
    parser.add_argument("--site-packages", type=Path, help="Directory containing the py-dem-bones wheel installation")
    parser.add_argument(
        "--two-bones", action="store_true", help="Also solve two disconnected, independently moving cubes"
    )
    parser.add_argument("--tolerance", type=float, default=1e-6, help="Maximum reconstruction RMSE in Maya world units")
    args = parser.parse_args(argv)
    if not 0 < args.tolerance < float("inf"):
        parser.error("--tolerance must be a positive finite number")
    if args.site_packages is not None:
        if not args.site_packages.is_dir():
            parser.error("--site-packages must be an existing directory")
        sys.path.insert(0, str(args.site_packages.resolve()))

    report = {"success": False, "plugin_loaded": False, "cases": []}
    standalone = None
    cmds = None
    initialized = False
    loaded_plugins = []
    try:
        import maya.standalone as standalone

        standalone.initialize(name="python")
        initialized = True
        import maya.api.OpenMaya as om
        import maya.cmds as cmds
        import numpy as np

        import py_dem_bones

        report["maya_version"] = cmds.about(version=True)
        report["package_version"] = py_dem_bones.__version__
        loaded_plugins = cmds.loadPlugin(args.plugin, quiet=True) or [args.plugin]
        report["plugin_loaded"] = all(cmds.pluginInfo(plugin, query=True, loaded=True) for plugin in loaded_plugins)
        if not report["plugin_loaded"]:
            raise RuntimeError("DCC-MCP Maya plugin did not load")
        for bone_count in ([1, 2] if args.two_bones else [1]):
            report["cases"].append(_solve_case(bone_count, cmds, om, np, py_dem_bones.solve_skinning, args.tolerance))
        report["success"] = True
    except Exception as exc:
        report["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        cleanup_errors = []
        if cmds is not None:
            for plugin in reversed(loaded_plugins):
                try:
                    cmds.unloadPlugin(plugin, force=True)
                except Exception as exc:
                    cleanup_errors.append(f"unload: {type(exc).__name__}: {exc}")
        if initialized:
            try:
                standalone.uninitialize()
            except Exception as exc:
                cleanup_errors.append(f"uninitialize: {type(exc).__name__}: {exc}")
        report["cleanup_succeeded"] = not cleanup_errors
        if cleanup_errors:
            report["cleanup_errors"] = cleanup_errors
            report["success"] = False
    print(json.dumps(report, separators=(",", ":"), allow_nan=False), flush=True)
    return 0 if report["success"] else 1


if __name__ == "__main__":
    sys.exit(main())

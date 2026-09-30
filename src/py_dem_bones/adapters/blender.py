"""Blender evaluated-mesh sampling and vertex-group weight writes."""

# Import third-party modules
import numpy as np

# Import local modules
from py_dem_bones.adapters.base import HostAdapter


class BlenderDCCInterface(HostAdapter):
    """Solve in Blender's current space using column-vector transformations.

    Export returns a dictionary, not the legacy boolean. Only named deform-bone
    vertex groups are written. The caller owns armature modifiers, bind/hierarchy
    handling, and animation authoring from the returned transformations.
    """

    def __init__(self, dem_bones_instance=None):
        super().__init__(dem_bones_instance)
        self._blender_data = {}

    def get_dcc_info(self):
        return {
            "name": "Blender", "version": "Host provided",
            "coordinate_system": "Host space; column-vector matrices",
        }

    @staticmethod
    def _topology(mesh):
        return len(mesh.vertices), tuple(tuple(int(index) for index in polygon.vertices) for polygon in mesh.polygons)

    @staticmethod
    def _bones(armature):
        return [bone.name for bone in armature.data.bones if bone.use_deform]

    @staticmethod
    def _objects(bpy, obj_name, armature_name):
        obj = bpy.data.objects.get(obj_name)
        armature = bpy.data.objects.get(armature_name)
        if obj is None or obj.type != "MESH" or armature is None or armature.type != "ARMATURE":
            raise ValueError("Expected an existing mesh and armature")
        if obj.mode != "OBJECT":
            raise ValueError("Mesh must be in Object mode")
        return obj, armature

    @classmethod
    def _sample_mesh(cls, bpy, obj, world_space):
        bpy.context.view_layer.update()
        evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
        mesh = evaluated.to_mesh()
        try:
            if mesh is None:
                raise ValueError("Blender did not produce an evaluated mesh")
            coordinates = [evaluated.matrix_world @ vertex.co if world_space else vertex.co for vertex in mesh.vertices]
            points = np.asarray([tuple(point) for point in coordinates], dtype=float)
            return points, cls._topology(mesh)
        finally:
            evaluated.to_mesh_clear()

    def from_dcc_data(self, obj_name, armature_name, shape_key_names=None, **kwargs):
        """Sample Basis and individual relative shape keys through the depsgraph.

        Shape-key values are restored on success and failure. Topology-changing
        modifiers are rejected because evaluated vertex IDs cannot safely address
        original vertex groups. Callers must preserve indexed vertex identity in
        modifiers which keep identical connectivity. Omitted keys mean one frame.
        """
        self._begin_import()
        self._blender_data = {}
        try:
            # Import third-party modules
            import bpy

            obj, armature = self._objects(bpy, obj_name, armature_name)
            names = list(shape_key_names or [])
            keys = obj.data.shape_keys
            if names and (keys is None or not keys.use_relative):
                raise ValueError("Requested poses require relative shape keys")
            if keys is not None and not keys.use_relative:
                raise ValueError("Absolute shape keys are unsupported")
            if len(set(names)) != len(names):
                raise ValueError("Shape-key names must be unique")
            blocks = list(keys.key_blocks) if keys is not None else []
            by_name = {key.name: key for key in blocks}
            for name in names:
                if name not in by_name or by_name[name].mute:
                    raise ValueError("Requested shape key is missing or muted: {}".format(name))
            original_values = [key.value for key in blocks]
            original_show_only = obj.show_only_shape_key
            world_space = kwargs.get("use_world_space", True)
            topology = self._topology(obj.data)
            try:
                obj.show_only_shape_key = False
                for key in blocks:
                    key.value = 0.0
                rest, evaluated_topology = self._sample_mesh(bpy, obj, world_space)
                if any(key.value != 0.0 for key in blocks):
                    raise ValueError("Shape-key drivers override requested sample values")
                if evaluated_topology != topology:
                    raise ValueError("Evaluated topology differs from original vertex-group topology")
                poses = []
                for name in names:
                    by_name[name].value = 1.0
                    points, pose_topology = self._sample_mesh(bpy, obj, world_space)
                    if any(key.value != float(key.name == name) for key in blocks):
                        raise ValueError("Shape-key drivers override requested sample values")
                    if pose_topology != topology:
                        raise ValueError("Shape-key pose changes indexed mesh topology: {}".format(name))
                    poses.append(points)
                    by_name[name].value = 0.0
            finally:
                for key, value in zip(blocks, original_values):
                    key.value = value
                obj.show_only_shape_key = original_show_only
                bpy.context.view_layer.update()
            bones = self._bones(armature)
            imported = self._import_sequence(
                rest, poses or [rest.copy()], bones, topology[1],
                max_influences=kwargs.get("max_influences", 4),
                smooth_iterations=kwargs.get("smooth_iterations", 3),
            )
            if not imported:
                return False
            self._blender_data = {
                "obj_name": obj_name, "armature_name": armature_name,
                "object_id": obj.as_pointer(), "mesh_id": obj.data.as_pointer(),
                "armature_id": armature.as_pointer(), "armature_data_id": armature.data.as_pointer(),
                "bones": bones, "topology": topology, "world_space": world_space,
            }
            return True
        except Exception as exc:
            self._begin_import()
            self._blender_data = {}
            self._failure(exc)
            return False

    def to_dcc_data(self, apply_weights=True, **kwargs):
        """Return the result and optionally replace every target group's weight.

        Unrelated groups remain untouched. ``create_vertex_groups`` defaults to
        True; when False all target groups must already exist. The legacy
        ``clear_existing_weights`` flag no longer deletes any vertex groups:
        full replacement always clears stale target weights, including zeros.
        No armature modifier or animation is created automatically.
        """
        result = self._export_result()
        if not result.get("success") or not apply_weights:
            return result
        try:
            # Import third-party modules
            import bpy

            data = self._blender_data
            obj, armature = self._objects(bpy, data["obj_name"], data["armature_name"])
            if (obj.as_pointer(), obj.data.as_pointer(), armature.as_pointer(), armature.data.as_pointer()) != (
                data["object_id"], data["mesh_id"], data["armature_id"], data["armature_data_id"],
            ):
                raise ValueError("Mesh or armature identity changed; reimport before writing weights")
            if self._topology(obj.data) != data["topology"]:
                raise ValueError("Mesh topology changed; reimport before writing weights")
            _, evaluated_topology = self._sample_mesh(bpy, obj, data["world_space"])
            if evaluated_topology != data["topology"]:
                raise ValueError("Evaluated topology changed; reimport before writing weights")
            bones = self._bones(armature)
            if bones != data["bones"] or bones != result["bone_names"]:
                raise ValueError("Deform-bone count or order changed; reimport before writing weights")
            groups = [obj.vertex_groups.get(name) for name in bones]
            if any(group is not None and group.lock_weight for group in groups):
                raise ValueError("Target vertex group is locked")
            if not kwargs.get("create_vertex_groups", True) and any(group is None for group in groups):
                raise ValueError("Target vertex group is missing and creation is disabled")
            for bone_index, (name, group) in enumerate(zip(bones, groups)):
                if group is None:
                    group = obj.vertex_groups.new(name=name)
                for vertex_index, weight in enumerate(result["weights"][bone_index]):
                    # REPLACE includes zero and arbitrarily small weights.
                    group.add([vertex_index], float(weight), "REPLACE")
            return result
        except Exception as exc:
            return self._failure(exc)

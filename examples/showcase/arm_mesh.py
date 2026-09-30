"""Extract an arm from the explicitly CC0 MakeHuman graphical base mesh."""

# Import standard library modules
from pathlib import Path

# Import third-party modules
import numpy as np


def read_obj(path):
    points, faces = [], []
    group = "body"
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        fields = line.split()
        if not fields:
            continue
        if fields[0] == "v":
            points.append(tuple(map(float, fields[1:4])))
        elif fields[0] == "g":
            group = fields[1]
        elif fields[0] == "f" and group == "body":
            faces.append(tuple(int(item.split("/")[0]) - 1 for item in fields[1:]))
    return np.asarray(points), faces


def joint_positions(path):
    points, groups = [], {}
    group = ""
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        fields = line.split()
        if not fields:
            continue
        if fields[0] == "v":
            points.append(tuple(map(float, fields[1:4])))
        elif fields[0] == "g":
            group = fields[1]
        elif fields[0] == "f" and group.startswith("joint-"):
            groups.setdefault(group, set()).update(int(item.split("/")[0]) - 1 for item in fields[1:])
    points = np.asarray(points)
    return {name: points[sorted(indices)].mean(axis=0) for name, indices in groups.items()}


def extract_arm(source, destination, shoulder_x=2.0):
    points, faces = read_obj(source)
    vertices, arm_faces, mapping = [], [], {}
    for face in faces:
        polygon = [points[index] for index in face]
        for axis, threshold in ((0, shoulder_x), (1, 0.5)):
            clipped = []
            for start, end in zip(polygon, polygon[1:] + polygon[:1]):
                inside_start, inside_end = start[axis] >= threshold, end[axis] >= threshold
                if inside_start:
                    clipped.append(start)
                if inside_start != inside_end:
                    fraction = (threshold - start[axis]) / (end[axis] - start[axis])
                    clipped.append(start + fraction * (end - start))
            polygon = clipped
        if len(polygon) < 3:
            continue
        indices = []
        for point in polygon:
            key = tuple(np.round(point, 9))
            if key not in mapping:
                mapping[key] = len(vertices)
                vertices.append(point)
            indices.append(mapping[key])
        arm_faces.append(tuple(indices))
    arm = np.asarray(vertices)
    edges = {}
    for face in arm_faces:
        for start, end in zip(face, face[1:] + face[:1]):
            key = tuple(sorted((start, end)))
            edges.setdefault(key, []).append((start, end))
    boundary = {
        end: start
        for adjacent in edges.values()
        if len(adjacent) == 1
        for start, end in adjacent
        if np.allclose(arm[[start, end], 0], shoulder_x)
    }
    if boundary:
        first = next(iter(boundary))
        loop = [first]
        while boundary[loop[-1]] != first:
            loop.append(boundary[loop[-1]])
            if len(loop) > len(boundary):
                raise ValueError("Arm shoulder boundary is not one closed loop")
        if len(loop) != len(boundary):
            raise ValueError("Arm extraction has multiple shoulder boundaries")
        arm_faces.append(tuple(loop))
    lines = ["# CC0 MakeHuman base mesh arm extract; see SOURCE.json", "g body"]
    lines.extend("v %.9g %.9g %.9g" % tuple(point) for point in arm)
    lines.extend("f " + " ".join(str(index + 1) for index in face) for face in arm_faces)
    Path(destination).write_text("\n".join(lines) + "\n", encoding="utf-8")
    return arm, arm_faces

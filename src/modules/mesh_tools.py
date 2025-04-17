import numpy as np
from shapely.geometry import Polygon
from modules.obj_utils import generate_obj_text, extract_mesh

def face_normal(v0, v1, v2):
    normal = np.cross(v1 - v0, v2 - v0)
    norm = np.linalg.norm(normal)
    return normal / norm if norm > 1e-6 else normal

def share_edge(f1, f2):
    return list(set(f1) & set(f2))

def merge_triangles(log, vertices, faces, threshold=0.99):
    merged = []
    used = set()

    for i in range(len(faces)):
        if i in used:
            continue
        f1 = faces[i]
        if len(f1) != 3:
            merged.append(f1)
            used.add(i)
            continue
        v1 = [vertices[idx] for idx in f1]
        n1 = face_normal(*v1)

        merged_this_round = False

        for j in range(i + 1, len(faces)):
            if j in used:
                continue
            f2 = faces[j]
            shared = share_edge(f1, f2)
            if len(shared) != 2:
                continue  # not an adjacent triangle

            v2 = [vertices[idx] for idx in f2]
            n2 = face_normal(*v2)
            dot = np.dot(n1, n2)

            if dot >= threshold:
                # Merge triangles
                unique_indices = list(dict.fromkeys(f1 + f2))  # preserve order
                if len(unique_indices) == 4:
                    merged.append(unique_indices)
                    used.update([i, j])
                    merged_this_round = True
                    break

        if not merged_this_round:
            merged.append(f1)

    logstring = f'Merging Triangular Faces.'  + \
        f'\n    Original Unique Faces: {len(faces)}' + \
        f'\n    Final Unique Faces: {len(merged)}' + \
        f'\n    Merged Faces: {len(faces) - len(merged)}'
    log(logstring)
    return merged

def merge_coplanar_triangles_in_obj(log, obj_text, threshold=0.99):
    vertices, faces = extract_mesh(obj_text)
    merged_faces = merge_triangles(log, vertices, faces, threshold)
    return generate_obj_text(vertices, merged_faces)

def are_coplanar(v0, v1, v2, v3, tol=1e-6):
    # Check if point v3 lies on the plane defined by v0, v1, v2
    normal = np.cross(v1 - v0, v2 - v0)
    return abs(np.dot(v3 - v0, normal)) < tol

def project_to_plane(face_vertices):
    # Project 3D polygon onto best-fit 2D plane (assume planar)
    v0, v1, v2 = face_vertices[:3]
    x_axis = v1 - v0
    x_axis /= np.linalg.norm(x_axis)
    normal = np.cross(x_axis, v2 - v0)
    normal /= np.linalg.norm(normal)
    y_axis = np.cross(normal, x_axis)
    proj = []
    for v in face_vertices:
        rel = v - v0
        proj.append([np.dot(rel, x_axis), np.dot(rel, y_axis)])
    return proj

def remove_subfaces(vertices, faces):
    keep = [True] * len(faces)

    for i, a_indices in enumerate(faces):
        if not keep[i] or len(a_indices) < 3:
            continue
        a_verts = np.array([vertices[j] for j in a_indices])
        a_proj = project_to_plane(a_verts)
        a_poly = Polygon(a_proj)
        if not a_poly.is_valid:
            continue

        for j, b_indices in enumerate(faces):
            if i == j or not keep[j] or len(b_indices) < 3:
                continue
            b_verts = np.array([vertices[k] for k in b_indices])
            if not all(are_coplanar(a_verts[0], a_verts[1], a_verts[2], v) for v in b_verts):
                continue
            b_proj = project_to_plane(b_verts)
            b_poly = Polygon(b_proj)
            if not b_poly.is_valid:
                continue

            # If face j is entirely inside face i, drop it
            if a_poly.contains(b_poly):
                keep[j] = False

    return [f for f, k in zip(faces, keep) if k]

def compare_vertex(v1, v2):
    return v1[0] == v2[0] and v1[1] == v2[1] and v1[2] == v2[2]

def compare_faces(f1, f2, vertices):
    if not len(f1) == len(f2):
        return False
    f1_sorted = sorted(f1)
    f2_sorted = sorted(f2)
    for v1, v2 in zip(f1_sorted, f2_sorted):
        if not compare_vertex(vertices[v1], vertices[v2]):
            return False
    return True

def remove_duplicate_faces(log, vertices, faces):
    unique_faces = []
    for f1 in faces:
        dupe = False
        for f2 in unique_faces:
            if compare_faces(f1, f2, vertices):
                dupe = True
        if not dupe:
            unique_faces.append(f1)
    logstring = f'Removing Duplicate Faces:' +\
        f'\n    Original Unique Faces: {len(faces)}' +\
        f'\n    Final Unique Faces: {len(unique_faces)}' +\
        f'\n    Duplicate Faces Removed: {len(faces) - len(unique_faces)}'
    log(logstring)
    return unique_faces

def snap_vertex(vertex, snap_size=0.0625):
    return tuple(snap_size * round(val / snap_size) for val in vertex)

def clean_mesh(log, content):
    vertices, faces = extract_mesh(content)
    faces_clean = remove_subfaces(vertices, faces)
    unique_faces = remove_duplicate_faces(log, vertices, faces_clean)
    return generate_obj_text(vertices, unique_faces)

def combine_meshes(log, obj_texts, snap_enabled=False, snap_size=0.0625):
    all_faces = []

    vertex_map = {}  # maps vertex tuple -> new global index
    unique_vertices = []
    current_index = 0

    total_original_vertices = 0

    for text in obj_texts:
        local_vertices = []
        local_faces = []

        lines = text.strip().splitlines()
        for line in lines:
            if line.startswith('v '):
                parts = line.strip().split()
                vertex = tuple(map(float, parts[1:4]))
                if snap_enabled:
                    vertex = snap_vertex(vertex, snap_size)
                local_vertices.append(vertex)
            elif line.startswith('f '):
                parts = line.strip().split()
                face = [int(p.split('/')[0]) - 1 for p in parts[1:]]  # OBJ is 1-based
                local_faces.append(face)

        total_original_vertices += len(local_vertices)

        # Map local vertices to global deduplicated vertices
        remap = {}
        for i, v in enumerate(local_vertices):
            if v not in vertex_map:
                vertex_map[v] = current_index
                unique_vertices.append(v)
                current_index += 1
            remap[i] = vertex_map[v]

        # Remap local face indices to global indices
        for face in local_faces:
            try:
                new_face = [remap[i] for i in face]
                all_faces.append(new_face)
            except KeyError as e:
                print(f"[WARN] Face references missing vertex index {e}, skipping face: {face}")

    # Final counts
    final_vertex_count = len(unique_vertices)

    logstring = f'Merging {len(obj_texts)} OBJ files.'  + \
        f'\n    Original Unique Vertices: {total_original_vertices}' + \
        f'\n    Combined Unique Vertices: {final_vertex_count}' + \
        f'\n    Merged Vertices: {total_original_vertices - final_vertex_count}'
    log(logstring)

    # Reconstruct final obj
    lines = []
    for v in unique_vertices:
        lines.append(f"v {v[0]} {v[1]} {v[2]}")
    for face in all_faces:
        face_indices = [str(i + 1) for i in face]  # back to 1-based
        lines.append(f"f {' '.join(face_indices)}")

    return '\n'.join(lines)
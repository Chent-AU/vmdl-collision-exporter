import os
import re
import numpy as np
from shapely.geometry import Polygon

def extract_dmx_values(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    verticies = extract_vertex_data(content)
    faces = extract_face_groups(content)
    return [verticies, faces]

def extract_vertex_data(content):
    # Regex to extract the vertexFormat string_array
    
    vertex_format_re = re.search(r'"vertexFormat"\s+"string_array"\s+\[\s*(.*?)\s*\]', content, re.DOTALL)
    if not vertex_format_re:
        return {}

    # Extract elements like "position$0", "texcoord$0", etc.
    vertex_types = re.findall(r'"([^"]+)"', vertex_format_re.group(1))

    # Strip down to base type names like 'position', 'texcoord', etc.
    base_types = [vt.split('$')[0] for vt in vertex_types]

    result = {}

    for base_type in base_types:
        value_key = f'{base_type}$0'
        index_key = f'{base_type}$0Indices'

        # Extract data block for this type
        value_match = re.search(rf'"{re.escape(value_key)}"\s+"[^"]*"\s+\[\s*(.*?)\s*\]', content, re.DOTALL)
        index_match = re.search(rf'"{re.escape(index_key)}"\s+"int_array"\s+\[\s*(.*?)\s*\]', content, re.DOTALL)

        if value_match and index_match:
            raw_values = re.findall(r'"([^"]+)"', value_match.group(1))
            raw_indices = re.findall(r'"(\d+)"', index_match.group(1))

            values = [list(map(float, v.split())) for v in raw_values]
            indices = list(map(int, raw_indices))

            result[base_type] = values
            
    return result

def extract_data_from_obj(text):
    vertices = []
    faces = []

    lines = text.split('\n')
    for line in lines:
        if line.startswith('v '):
            parts = line.strip().split()
            vertex = list(map(float, parts[1:4]))
            vertices.append(vertex)
        elif line.startswith('f '):
            parts = line.strip().split()
            indices = [int(p.split('/')[0]) - 1 for p in parts[1:]]  # OBJ is 1-based
            faces.append(indices)

    return np.array(vertices), faces

def face_normal(v0, v1, v2):
    normal = np.cross(v1 - v0, v2 - v0)
    norm = np.linalg.norm(normal)
    return normal / norm if norm > 1e-6 else normal

def share_edge(f1, f2):
    return list(set(f1) & set(f2))

def merge_triangles(vertices, faces, threshold=0.99):
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

    return merged

def merge_coplanar_triangles_in_obj(obj_text, threshold=0.99):
    vertices, faces = extract_data_from_obj(obj_text)
    merged_faces = merge_triangles(vertices, faces, threshold)
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

def clean_obj_file(path):
    vertices, faces = extract_data_from_obj(path)
    faces_clean = remove_subfaces(vertices, faces)
    return generate_obj_text(vertices, faces_clean)
        
def extract_face_groups(content):
    pattern = r'"faces"\s*"int_array"\s*\[\s*((?:"-?\d+",?\s*)+)\]'
    matches = re.findall(pattern, content)

    all_faces = []
    for match in matches:
        numbers = re.findall(r'"(-?\d+)"', match)
        current_face = []
        for num in numbers:
            val = int(num)
            if val == -1:
                if current_face:
                    all_faces.append(current_face)
                    current_face = []
            else:
                current_face.append(val)

    return all_faces


def generate_obj_text(vertices, faces):
    lines = []
    # Write vertex positions
    for v in vertices:
        lines.append(f"v {v[0]} {v[1]} {v[2]}")

    # Write faces (indices in OBJ are 1-based)
    for face in faces:
        face_indices = [str(i + 1) for i in face]
        lines.append(f"f {' '.join(face_indices)}")

    return '\n'.join(lines)

def combine_objs(obj_texts):
    all_faces = []

    vertex_map = {}  # maps vertex tuple -> new global index
    unique_vertices = []
    current_index = 0

    for text in obj_texts:
        local_vertices = []
        local_faces = []

        lines = text.strip().splitlines()
        for line in lines:
            if line.startswith('v '):
                parts = line.strip().split()
                vertex = tuple(map(float, parts[1:4]))
                local_vertices.append(vertex)
            elif line.startswith('f '):
                parts = line.strip().split()
                face = [int(p.split('/')[0]) - 1 for p in parts[1:]]  # OBJ is 1-based
                local_faces.append(face)

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

    # Reconstruct final obj
    lines = []
    for v in unique_vertices:
        lines.append(f"v {v[0]} {v[1]} {v[2]}")
    for face in all_faces:
        face_indices = [str(i + 1) for i in face]  # back to 1-based
        lines.append(f"f {' '.join(face_indices)}")

    return '\n'.join(lines)


def extract_dmx_paths_from_vmdl(vmdl_path):
    with open(vmdl_path, 'r', encoding='utf-8') as f:
        content = f.read()

    render = [os.path.basename(dmx) for dmx in re.findall(r'RenderMeshFile".*?filename\s*=\s*"([^"]+\.dmx)"', content, re.DOTALL)]
    physics = [os.path.basename(dmx) for dmx in re.findall(r'PhysicsHullFile".*?filename\s*=\s*"([^"]+\.dmx)"', content, re.DOTALL)]
    return render, physics

def construct_obj_from_vmdl(log, vmdl_path, base_dir, output_path, merge_threshold=1, use_physics=False, use_render=False, combine_physics_and_render=True):
    basename = os.path.basename(vmdl_path).split('.')[0]
    render_list, physics_list = extract_dmx_paths_from_vmdl(vmdl_path)

    render_obj_texts = []
    if use_render or combine_physics_and_render:
        for path in render_list:
            full_path = os.path.join(base_dir, path)
            vertices, faces = extract_dmx_values(full_path)
            all_vertex_formats = [ "position", "texcoord", "normal", "tangent" ]
            vertex_positions = vertices["position"]
            log(f'Generating obj for render dmx file: {path}')
            render_obj_texts.append(generate_obj_text(vertex_positions, faces))

    physics_obj_texts = []
    if use_physics or combine_physics_and_render:
        for path in physics_list:
            full_path = os.path.join(base_dir, path)
            vertices, faces = extract_dmx_values(full_path)
            all_vertex_formats = [ "position", "texcoord", "normal", "tangent" ]
            vertex_positions = vertices["position"]
            log(f'Generating obj for physics dmx file: {path}')
            physics_obj_texts.append(generate_obj_text(vertex_positions, faces))
    
    
    if use_render and len(render_obj_texts) > 0:
        combined = combine_objs(render_obj_texts)
        merged_triangles = merge_coplanar_triangles_in_obj(combined, merge_threshold)
        cleaned = clean_obj_file(merged_triangles)
        write_obj(log, cleaned, output_path, basename, '.render')
    elif use_render:
        log(f'No render DMX paths found for vmdl: {basename}')
        
    if use_physics and len(physics_obj_texts) > 0:
        combined = combine_objs(physics_obj_texts)
        merged_triangles = merge_coplanar_triangles_in_obj(combined, merge_threshold)
        cleaned = clean_obj_file(merged_triangles)
        write_obj(log, cleaned, output_path, basename, '.physics')
    elif use_physics:
        log(f'No physics DMX paths found for vmdl: {basename}')
        
    if combine_physics_and_render and (len(render_obj_texts) > 0 or len(physics_obj_texts) > 0):
        all_objs = physics_obj_texts + render_obj_texts
        combined = combine_objs(all_objs)
        merged_triangles = merge_coplanar_triangles_in_obj(combined, merge_threshold)
        cleaned = clean_obj_file(merged_triangles)
        write_obj(log, cleaned, output_path, basename, '.combined')
        
        
def write_obj(log, data, base_path, basename, suffix=""):
    filepath = os.path.join(base_path, basename + suffix + '.obj')
    log(f'Writing obj file: {basename + suffix + ".obj"}')
    f = open(filepath, 'w')
    f.write(data)
    f.close()
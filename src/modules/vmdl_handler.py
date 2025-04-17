import os
import re
from modules.mesh_tools import merge_coplanar_triangles_in_obj, clean_mesh, combine_meshes
from modules.obj_utils import generate_obj_text
from modules.file_manager import write_obj

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

def extract_dmx_paths_from_vmdl(vmdl_path):
    with open(vmdl_path, 'r', encoding='utf-8') as f:
        content = f.read()

    render = [os.path.basename(dmx) for dmx in re.findall(r'RenderMeshFile".*?filename\s*=\s*"([^"]+\.dmx)"', content, re.DOTALL)]
    physics = [os.path.basename(dmx) for dmx in re.findall(r'PhysicsHullFile".*?filename\s*=\s*"([^"]+\.dmx)"', content, re.DOTALL)]
    return render, physics

async def construct_objs_from_vmdls(callback, log, vmdl_paths, base_dir, output_path, merge_threshold=1, use_physics=False, use_render=False, combine_physics_and_render=True, snap_enabled=False, snap_size=0.0625):
    for path in vmdl_paths:
        construct_obj_from_vmdl(log, path, base_dir, output_path, merge_threshold, use_physics, use_render, combine_physics_and_render, snap_enabled, snap_size)
        
    callback(base_dir)

def construct_obj_from_vmdl(log, vmdl_path, base_dir, output_path, merge_threshold=1, use_physics=False, use_render=False, combine_physics_and_render=True, snap_enabled=False, snap_size=0.0625):
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
        combined = combine_meshes(log, render_obj_texts, snap_enabled, snap_size)
        merged_mesh = merge_coplanar_triangles_in_obj(log, combined, merge_threshold)
        cleaned = clean_mesh(log, merged_mesh)
        write_obj(log, cleaned, output_path, basename, '.render')
    elif use_render:
        log(f'No render DMX paths found for vmdl: {basename}')
        
    if use_physics and len(physics_obj_texts) > 0:
        combined = combine_meshes(log, physics_obj_texts, snap_enabled, snap_size)
        mergedmerged_mesh_triangles = merge_coplanar_triangles_in_obj(log, combined, merge_threshold)
        cleaned = clean_mesh(log, merged_mesh)
        write_obj(log, cleaned, output_path, basename, '.physics')
    elif use_physics:
        log(f'No physics DMX paths found for vmdl: {basename}')
        
    if combine_physics_and_render and (len(render_obj_texts) > 0 or len(physics_obj_texts) > 0):
        all_objs = physics_obj_texts + render_obj_texts
        combined = combine_meshes(log, all_objs, snap_enabled, snap_size)
        merged_mesh = merge_coplanar_triangles_in_obj(log, combined, merge_threshold)
        cleaned = clean_mesh(log, merged_mesh)
        write_obj(log, cleaned, output_path, basename, '.combined')
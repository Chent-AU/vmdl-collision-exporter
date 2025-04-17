import os
import glob
import shutil

def extract_addons(log, game_dir):
    compiled_addons_dir = os.path.join(game_dir, 'game\csgo_addons')
    blacklist = ["addon_template", "vpks", "workshop_items"]

    addons = []
    for name in os.listdir(compiled_addons_dir):
        full_path = os.path.join(compiled_addons_dir, name)
        if os.path.isdir(full_path) and name not in blacklist:
            addons.append(full_path)
            
    return addons

def copy_tree(source, dest):
    if not os.path.isdir(source):
        raise ValueError(f"Source path '{source}' is not a valid directory.")
    
    for root, dirs, _ in os.walk(source):
        if root == source:
            continue
        rel_path = os.path.relpath(root, source)
        dest_path = os.path.join(dest, rel_path)
        os.makedirs(dest_path, exist_ok=True)

def extract_vmdlc_from_dir(log, dir_path):
    vmdl_files = glob.glob(os.path.join(dir_path, '**', '*.vmdl_c'), recursive=True)
    for vmdl_path in vmdl_files:
        log(f'.vmdl_c found: {vmdl_path}')

    return vmdl_files

def extract_vmdl_from_dir(log, dir_path):
    vmdl_files = glob.glob(os.path.join(dir_path, '**', '*.vmdl'), recursive=True)
    for vmdl_path in vmdl_files:
        log(f'.vmdl found: {vmdl_path}')

    return vmdl_files

def extract_gltf_from_dir(log, dir_path):
    gltf_files = glob.glob(os.path.join(dir_path, '**', '*.glb'), recursive=True)
    for gltf_path in gltf_files:
        log(f'.glb found: {gltf_path}')

    return gltf_files

def copy_files_with_index(log, filepaths, output_dir):
    new_filepaths = []
    for index, file_path in enumerate(filepaths):
        if not os.path.isfile(file_path):
            log(f'Skipping .vmdl_c fp: {file_path} is not a file.')
            continue  # Skip if it's not a file
        filename = os.path.basename(file_path)
        new_filename = f"{index}_{filename}"
        dest_path = os.path.join(output_dir, new_filename)
        new_filepaths.append(dest_path)
        shutil.copy2(file_path, dest_path)
    return new_filepaths

def write_obj(log, data, base_path, basename, suffix=""):
    filepath = os.path.join(base_path, basename + suffix + '.obj')
    log(f'Writing obj file: {basename + suffix + ".obj"}')
    f = open(filepath, 'w')
    f.write(data)
    f.close()
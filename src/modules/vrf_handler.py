import os
import subprocess
import shutil
import glob

def find_vrf_folder(start_dir=None):
    current_dir = os.path.abspath(start_dir or os.getcwd())

    while True:
        # Search current level and subdirectories
        for root, dirs, _ in os.walk(current_dir):
            if 'vrf' in dirs:
                return os.path.join(root, 'vrf', 'Source2Viewer-CLI.exe')

        # Go up one directory level
        parent_dir = os.path.dirname(current_dir)
        if parent_dir == current_dir:
            # Reached root and didn't find it
            return None
        current_dir = parent_dir

def decomp_vmdl_cs(log, input_dir, output_dir):
    vrf_tool_path = find_vrf_folder()
    if not vrf_tool_path or not os.path.exists(vrf_tool_path):
        raise FileNotFoundError("Could not locate Source2Viewer-CLI.exe in any 'vrf' folder.")

    gltf_files = []
    # print_str = '\n    ' + '\n    '.join(vmdl_files)
    # log(f'Attempting to convert files: {print_str}')
    result = subprocess.run([
            vrf_tool_path,
            "--input", input_dir,
            "--vpk_decompile",
            "--vpk_extensions", "vmdl_c",
            "--recursive",
            "--recursive_vpk",
            "--output", output_dir
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
            log(f"❌ Failed to convert {input_dir}\n{result.stderr}\n{result.stdout}")
    log(f'{result.stdout}')
    return

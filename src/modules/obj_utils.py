import numpy as np

def extract_mesh(text):
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
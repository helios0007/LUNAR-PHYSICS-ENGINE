import trimesh
import numpy as np

def parse_habitat(filepath):
    mesh = trimesh.load(filepath)

    print(f"Faces:        {len(mesh.faces)}")
    print(f"Vertices:     {len(mesh.vertices)}")
    print(f"Volume (m³):  {mesh.volume:.4f}")
    print(f"Watertight:   {mesh.is_watertight}")

    normals   = mesh.face_normals
    centroids = mesh.triangles_center
    areas     = mesh.area_faces

    print(f"Sample normal:      {normals[0]}")
    print(f"Total surface area: {areas.sum():.4f} m²")

    return {
        "mesh":      mesh,
        "normals":   normals,
        "centroids": centroids,
        "areas":     areas
    }
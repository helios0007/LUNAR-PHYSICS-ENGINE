import trimesh
import numpy as np

def group_faces_by_normal(mesh, tolerance=0.01):
    """Groups triangles that share the same normal direction into logical walls."""
    normals = mesh.face_normals
    centroids = mesh.triangles_center
    groups = {}

    for i, normal in enumerate(normals):
        # Round normal to tolerance to group near-identical directions
        key = tuple(np.round(normal / (tolerance + 1e-9) * tolerance, 2))
        if key not in groups:
            groups[key] = {
                "normal": normal,
                "face_indices": [],
                "area": 0.0,
                "centroid": np.zeros(3),  # accumulated area-weighted centroid
            }
        face_area = mesh.area_faces[i]
        groups[key]["face_indices"].append(i)
        groups[key]["area"] += face_area
        # Accumulate area-weighted centroid; divide by total area after loop
        groups[key]["centroid"] += centroids[i] * face_area

    walls = list(groups.values())
    for wall in walls:
        wall["centroid"] /= wall["area"]  # normalise to get true area-weighted centre

    return walls


def parse_habitat(filepath):
    mesh = trimesh.load(filepath)
    mesh.apply_scale(0.001)  # mm → metres

    print(f"Faces (triangles): {len(mesh.faces)}")
    print(f"Vertices:          {len(mesh.vertices)}")
    print(f"Volume (m³):       {mesh.volume:.4f}")
    print(f"Watertight:        {mesh.is_watertight}")
    print(f"Total surface area:{mesh.area_faces.sum():.4f} m²")

    # Group into logical walls
    walls = group_faces_by_normal(mesh)
    print(f"\nLogical walls detected: {len(walls)}")
    for i, wall in enumerate(walls):
        print(f"  Wall {i+1}: normal={np.round(wall['normal'], 2)}  area={wall['area']:.4f} m²")

    return {
        "mesh":      mesh,
        "normals":   mesh.face_normals,
        "centroids": mesh.triangles_center,
        "areas":     mesh.area_faces,
        "walls":     walls        # ← new: logical wall groups
    }
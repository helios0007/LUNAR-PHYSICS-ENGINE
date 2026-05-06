import numpy as np
import trimesh
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from mpl_toolkits.mplot3d.art3d import Poly3DCollection


def generate_ray_directions(num_rays=500):
    """
    Generate evenly distributed directions on a sphere
    using the Fibonacci sphere method.
    """
    indices = np.arange(num_rays, dtype=float)

    phi = np.arccos(1 - 2 * indices / num_rays)
    theta = np.pi * (1 + 5**0.5) * indices

    x = np.sin(phi) * np.cos(theta)
    y = np.sin(phi) * np.sin(theta)
    z = np.cos(phi)

    return np.column_stack((x, y, z))


def cast_rays(model_data):
    """
    Cast rays from each logical wall's centroid inward to estimate
    shielding thickness per wall surface.
    """

    mesh  = model_data["mesh"]
    walls = model_data["walls"]   # list of wall dicts from group_faces_by_normal

    all_directions = generate_ray_directions(500)

    results = []

    print(f"Starting ray casting over {len(walls)} walls...")

    for i, wall in enumerate(walls):
        wall_normal = wall["normal"]
        centroid    = wall["centroid"]

        # Keep only directions in the outward hemisphere of this wall so that
        # -direction always shoots inward through the structure.
        dots       = all_directions @ wall_normal
        inward_dirs = all_directions[dots > 0]

        total_thickness = 0.0
        valid_count     = 0

        for direction in inward_dirs:

            ray_origin = centroid + direction * 0.001
            ray_dir    = -direction

            locations, _, _ = mesh.ray.intersects_location(
                ray_origins=[ray_origin],
                ray_directions=[ray_dir]
            )

            if len(locations) >= 2:
                thickness = np.linalg.norm(locations[1] - locations[0])
                total_thickness += thickness
                valid_count += 1

        avg_thickness = total_thickness / valid_count if valid_count > 0 else 0.0

        results.append({
            "wall_index":      i,
            "face_indices":    wall["face_indices"],   # all triangles that belong here
            "centroid":        centroid,
            "normal":          wall_normal,
            "area":            wall["area"],
            "avg_shielding_m": round(avg_thickness, 4)
        })

        print(f"  Wall {i + 1}/{len(walls)}  shielding={avg_thickness:.4f} m  "
              f"faces={len(wall['face_indices'])}  area={wall['area']:.3f} m²")

    print("Ray casting completed.")

    return results


def visualize_results(model_data, results):
    """
    Create a 3D heatmap visualization of shielding thickness.
    Every triangle that belongs to the same wall is painted the same colour
    so the model reads as discrete architectural surfaces, not a noisy triangle soup.
    """

    mesh = model_data["mesh"]

    # Build a per-triangle shielding lookup keyed by face index.
    # Every triangle in a wall inherits the wall's avg_shielding_m value.
    face_shielding = np.zeros(len(mesh.faces))
    for r in results:
        for fi in r["face_indices"]:
            face_shielding[fi] = r["avg_shielding_m"]

    min_v = face_shielding.min()
    max_v = face_shielding.max()
    norm  = (face_shielding - min_v) / (max_v - min_v + 1e-9)

    colormap = cm.RdYlGn

    polys  = []
    colors = []

    for i, face in enumerate(mesh.faces):
        polys.append(mesh.vertices[face])
        colors.append(colormap(norm[i]))

    fig = plt.figure(figsize=(10, 7))
    ax  = fig.add_subplot(111, projection='3d')

    collection = Poly3DCollection(polys, zsort='average')
    collection.set_facecolor(colors)
    collection.set_edgecolor('grey')
    collection.set_linewidth(0.2)

    ax.add_collection3d(collection)

    scale = mesh.vertices.flatten()
    ax.auto_scale_xyz(scale, scale, scale)

    ax.set_title("Shielding Heatmap — per wall surface (Red = Thin, Green = Thick)")
    ax.set_xlabel("X (m)")
    ax.set_ylabel("Y (m)")
    ax.set_zlabel("Z (m)")

    sm = cm.ScalarMappable(cmap=colormap)
    sm.set_array(face_shielding)
    plt.colorbar(sm, ax=ax, label="Average Shielding Thickness (m)", shrink=0.5)

    plt.tight_layout()
    plt.savefig("shielding_heatmap.png", dpi=150)
    plt.show()

    print("Saved visualization: shielding_heatmap.png")

    return results
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
    Cast rays from each face centroid inward to estimate
    shielding thickness.
    """

    mesh = model_data["mesh"]
    centroids = model_data["centroids"]

    directions = generate_ray_directions(500)

    results = []

    print("Starting ray casting...")

    for i, centroid in enumerate(centroids):

        total_thickness = 0

        for direction in directions:

            # Start ray slightly outside face
            ray_origin = centroid + direction * 0.001
            ray_dir = -direction

            locations, _, _ = mesh.ray.intersects_location(
                ray_origins=[ray_origin],
                ray_directions=[ray_dir]
            )

            if len(locations) >= 2:
                thickness = np.linalg.norm(locations[1] - locations[0])
                total_thickness += thickness

        avg_thickness = total_thickness / len(directions)

        results.append({
            "face_index": i,
            "centroid": centroid,
            "avg_shielding_m": round(avg_thickness, 4)
        })

        if i % 100 == 0:
            print(f"Processed face {i} / {len(centroids)}")

    print("Ray casting completed.")

    return results


def visualize_results(model_data, results):
    """
    Create a 3D heatmap visualization of shielding thickness.
    """

    mesh = model_data["mesh"]

    scores = {r["face_index"]: r["avg_shielding_m"] for r in results}

    values = [scores[i] for i in range(len(mesh.faces))]

    min_v = min(values)
    max_v = max(values)

    norm = [(v - min_v) / (max_v - min_v + 1e-9) for v in values]

    polys = []
    colors = []

    colormap = cm.RdYlGn

    for i, face in enumerate(mesh.faces):

        verts = mesh.vertices[face]

        polys.append(verts)

        colors.append(colormap(norm[i]))

    fig = plt.figure(figsize=(10, 7))
    ax = fig.add_subplot(111, projection='3d')

    collection = Poly3DCollection(polys, zsort='average')

    collection.set_facecolor(colors)
    collection.set_edgecolor('grey')
    collection.set_linewidth(0.2)

    ax.add_collection3d(collection)

    scale = mesh.vertices.flatten()

    ax.auto_scale_xyz(scale, scale, scale)

    ax.set_title("Shielding Heatmap (Red = Thin, Green = Thick)")
    ax.set_xlabel("X (m)")
    ax.set_ylabel("Y (m)")
    ax.set_zlabel("Z (m)")

    sm = cm.ScalarMappable(cmap=colormap)
    sm.set_array(values)

    plt.colorbar(
        sm,
        ax=ax,
        label="Average Shielding Thickness (m)",
        shrink=0.5
    )

    plt.tight_layout()

    plt.savefig("shielding_heatmap.png", dpi=150)

    plt.show()

    print("Saved visualization: shielding_heatmap.png")

    return results
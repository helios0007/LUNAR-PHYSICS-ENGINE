# LUNAR-PHYSICS-ENGINE

A physics-based radiation shielding analysis tool for lunar habitat architects. It takes a 3D model of a habitat, traces rays through the geometry to measure structural thickness at every surface point, and produces a color-coded heatmap identifying where the building is most vulnerable to radiation.

---

## What it does

Lunar habitats must protect occupants from two primary radiation threats:

- **Galactic Cosmic Rays (GCR)** — high-energy particles arriving continuously from all directions
- **Solar Particle Events (SPE)** — intense bursts from solar flares, directional from the sun

The thicker the surrounding structure, the more radiation is absorbed before reaching the interior. This tool maps structural thickness across every face of the habitat model so architects can see at a glance where shielding is inadequate.

---

## How it works

### 1. Load geometry (`parser.py`)

The habitat model (STL, OBJ, or any trimesh-supported format) is loaded and converted from millimeters to meters. The tool validates that the mesh is watertight — a necessary condition for accurate shielding measurement — and groups all triangular faces into logical walls based on their surface normals.

### 2. Generate ray directions (`ray_tracer.py`)

500 ray directions are distributed evenly across a full sphere using the **Fibonacci sphere method** (golden-ratio azimuthal offset). This guarantees uniform angular sampling with no clustering near the poles, which a purely random approach would suffer from.

### 3. Cast rays from every face (`ray_tracer.py`)

For each triangular face on the habitat surface:

- A ray origin is placed 1 mm outside the face centroid
- 500 rays are fired back through the structure, one per sample direction
- Each ray records all intersection points with the mesh
- The distance between the first two intersections (entry and exit through structure) is the **shielding thickness** in that direction
- These 500 measurements are averaged to produce a single `avg_shielding_m` value for the face

### 4. Rank and visualize results (`main.py`, `ray_tracer.py`)

Faces are sorted by shielding thickness, weakest first. The five most vulnerable faces are printed to the terminal. A 3D heatmap is rendered and saved as `shielding_heatmap.png`:

- **Red** — thin shielding, high radiation risk
- **Yellow** — moderate shielding
- **Green** — thick shielding, well protected

---

## Installation

```bash
pip install -r requirements.txt
```

Dependencies: `numpy`, `trimesh`, `rtree`, `matplotlib`

---

## Usage

```bash
python main.py path/to/habitat.stl
```

The tool accepts any mesh format supported by trimesh (STL, OBJ, PLY, GLTF, etc.). Input units are assumed to be **millimeters** and are converted to meters automatically.

### Example output

```
Faces (triangles):  1240
Vertices:           620
Volume (m³):        45.2300
Watertight:         True
Total surface area: 180.4400 m²

Logical walls detected: 12
  Wall 1: normal=[ 0.  0.  1.]  area=22.1500 m²
  Wall 2: normal=[ 0.  0. -1.]  area=22.1500 m²
  ...

Starting ray casting...
Processed face 0 / 1240
Processed face 100 / 1240
...
Ray casting completed.

--- Weakest shielded faces ---
Face 312: 0.0821 m avg thickness
Face 48:  0.0834 m avg thickness
Face 900: 0.0912 m avg thickness
Face 75:  0.0988 m avg thickness
Face 201: 0.1043 m avg thickness
```

A value of `0.08 m` (8 cm) of regolith or concrete is roughly the minimum considered for GCR shielding. SPE events require significantly more — typically 0.5 m or more of regolith equivalent.

---

## Project status

| Module | Status |
|---|---|
| Mesh loading and unit conversion | Complete |
| Watertight mesh validation | Complete |
| Wall grouping by surface normal | Complete |
| Fibonacci sphere ray distribution | Complete |
| Per-face thickness measurement | Complete |
| Weakness ranking and terminal report | Complete |
| 3D heatmap visualization + PNG export | Complete |
| Wall-level shielding summary | Not yet started |
| Radiation flux weighting (GCR / SPE model) | Not yet started |
| Material shielding factor (regolith vs concrete) | Not yet started |
| JSON / CSV export for downstream tools | Not yet started |
| Parallel ray casting | Not yet started |

---

## Changelog

### Bug fixes — ray_tracer.py `cast_rays`

**Problem 1 — Wrong hemisphere sampling**

Before the fix, 500 rays were fired in directions spread across the *full sphere* from each face centroid. Roughly half of those directions point *away from the structure* (outward through the face). When a ray starts just outside the surface and points further outward, it exits the mesh immediately with 0 or 1 intersections and contributes zero to the shielding average. This silently cut every face's reported shielding roughly in half — and worse, it affected curved or angled faces unevenly depending on how many rays happened to point in the wrong direction.

**Fix:** For each face, compute `dot(direction, face_normal)` for all 500 candidate directions using a single vectorised matrix multiply (`all_directions @ face_normal`). Keep only directions where the dot product is positive — those point outward from the face, so `-direction` points inward through the structure. Roughly 250 of the 500 rays survive this filter per face, all guaranteed to shoot through real material.

```python
# Before
for direction in directions:          # all 500, half are wrong

# After
dots = all_directions @ face_normal
inward_dirs = all_directions[dots > 0]  # ~250, all correct
for direction in inward_dirs:
```

---

**Problem 2 — Wrong averaging denominator**

The old code summed thickness over valid intersections but divided by `len(directions)` (always 500). Rays that produced 0 or 1 intersections contributed 0 to the numerator but were still counted in the denominator, artificially depressing the average.

**Fix:** Track a `valid_count` alongside `total_thickness`. Only increment `valid_count` when `len(locations) >= 2` (a genuine entry + exit measurement). Divide by `valid_count` at the end, with a zero guard for degenerate faces.

```python
# Before
avg_thickness = total_thickness / len(directions)   # denominator always 500

# After
avg_thickness = total_thickness / valid_count if valid_count > 0 else 0.0
```

**Combined effect:** The reported `avg_shielding_m` values now reflect the true average thickness through the structure for radiation coming from outside the habitat. Faces that were previously underreported (especially those on curved surfaces or at oblique angles) will now show higher, more accurate shielding values.

---

## Architecture

```
main.py           — orchestrates the pipeline
parser.py         — loads mesh, extracts geometry, groups faces into walls
ray_tracer.py     — Fibonacci ray generation, intersection testing, visualization
requirements.txt  — dependency list
```

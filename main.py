import sys
import numpy as np
from parser import parse_habitat
from ray_tracer import cast_rays, visualize_results

if __name__ == "__main__":
    filepath = sys.argv[1]

    model   = parse_habitat(filepath)
    results = cast_rays(model)

    sorted_results = sorted(results, key=lambda x: x["avg_shielding_m"])

    print("\n--- Weakest shielded walls ---")
    for wall in sorted_results[:5]:
        print(
            f"  Wall {wall['wall_index']:>3}  "
            f"{wall['avg_shielding_m']:.4f} m  "
            f"area={wall['area']:.3f} m²  "
            f"normal={np.round(wall['normal'], 2)}"
        )

    visualize_results(model, results)
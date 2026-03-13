import sys
from parser import parse_habitat
from ray_tracer import cast_rays, visualize_results

if __name__ == "__main__":
    filepath = sys.argv[1]

    model = parse_habitat(filepath)
    results = cast_rays(model)

    sorted_results = sorted(results, key=lambda x: x["avg_shielding_m"])

    print("\n--- Weakest shielded faces ---")
    for face in sorted_results[:5]:
        print(f"Face {face['face_index']}: {face['avg_shielding_m']} m avg thickness")

    visualize_results(model, results)
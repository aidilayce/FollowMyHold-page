#!/usr/bin/env python3
#!/usr/bin/env python3
# Force solid vertex colors on hand + object and export GLB for <model-viewer>.
# Usage:
#   python ply2glb_colors.py --hand hand.ply --object obj.ply --out public/models/example_v2.glb \
#       --hand-color 184,184,209,255 --obj-color 200,200,200,255 --mm

import argparse, numpy as np, trimesh
from pathlib import Path

def ensure_trimesh(g):
    if isinstance(g, trimesh.Scene):
        g = trimesh.util.concatenate([m for m in g.geometry.values()])
    assert isinstance(g, trimesh.Trimesh)
    return g

def parse_rgba(s, default):
    try:
        vals = [int(x) for x in s.split(",")]
        assert len(vals) in (3,4)
        if len(vals)==3: vals.append(255)
        return np.array(vals[:4], dtype=np.uint8)
    except Exception:
        return np.array(default, dtype=np.uint8)

def apply_solid_vertex_color(mesh: trimesh.Trimesh, rgba: np.ndarray):
    # overwrite ANY existing visuals/materials/textures
    mesh.visual = trimesh.visual.ColorVisuals(mesh, vertex_colors=np.tile(rgba, (len(mesh.vertices), 1)))
    # also remove per-face materials if any were lingering
    if hasattr(mesh, "material"):
        try:
            mesh.material = None  # not always present; ignore errors
        except Exception:
            pass

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hand", required=True, type=Path)
    ap.add_argument("--object", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--hand-color", default="116, 118, 145,255")
    ap.add_argument("--obj-color",  default="124, 154, 129,255")
    ap.add_argument("--mm", action="store_true", help="inputs are in millimeters; convert to meters")
    ap.add_argument("--center", action="store_true", help="re-center combined bbox at origin")
    ap.add_argument("--unit-scale", action="store_true", help="scale combined bbox max extent to 1.0")
    args = ap.parse_args()

    hand = ensure_trimesh(trimesh.load(args.hand, process=True))
    obj  = ensure_trimesh(trimesh.load(args.object, process=True))

    if args.mm:
        hand.apply_scale(0.001)
        obj.apply_scale(0.001)

    # Force vertex colors
    hc = parse_rgba(args.hand_color, [116, 118, 145,255])
    oc = parse_rgba(args.obj_color,  [124, 154, 129,255])
    apply_solid_vertex_color(hand, hc)
    apply_solid_vertex_color(obj,  oc)

    # Optional normalize together (preserve relative pose)
    if args.center or args.unit_scale:
        all_pts = np.vstack([hand.vertices, obj.vertices])
        min_b, max_b = all_pts.min(0), all_pts.max(0)
        center = 0.5 * (min_b + max_b)
        extent = float((max_b - min_b).max())
        if args.center:
            T = np.eye(4); T[:3,3] = -center
            hand.apply_transform(T); obj.apply_transform(T)
        if args.unit-scale and extent > 0:
            s = 1.0/extent
            hand.apply_scale(s); obj.apply_scale(s)

    scene = trimesh.Scene()
    scene.add_geometry(hand, node_name="hand")
    scene.add_geometry(obj,  node_name="object")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "wb") as f:
        f.write(scene.export(file_type="glb"))

    print(f"Wrote {args.out}")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Convert HAND.ply + OBJECT.ply -> single GLB for <model-viewer>.

Usage:
  python ply2glb.py --hand hand.ply --object obj.ply --out models/sample.glb
Options:
  --no-center         Do not recenter meshes to the origin
  --no-unit-scale     Do not scale to unit box (max extent = 1.0)
  --mm                Inputs are in millimeters (will convert to meters)
  --hand-color 180,200,255,255
  --obj-color  200,200,200,255
"""
import argparse, numpy as np, trimesh
from pathlib import Path

def _ensure_trimesh(g):
    # If a Scene was loaded (e.g., ASCII PLY with groups), merge to a Trimesh
    if isinstance(g, trimesh.Scene):
        g = trimesh.util.concatenate([m for m in g.geometry.values()])
    assert isinstance(g, trimesh.Trimesh), "Expected a single mesh or scene convertible to Trimesh"
    return g

def _parse_color(cstr, default):
    try:
        return np.fromstring(cstr, sep=',', dtype=np.uint8)
    except Exception:
        return np.array(default, dtype=np.uint8)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hand", required=True, type=Path)
    ap.add_argument("--object", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--no-center", action="store_true")
    ap.add_argument("--no-unit-scale", action="store_true")
    ap.add_argument("--mm", action="store_true", help="Convert mm to meters (scale 0.001)")
    ap.add_argument("--hand-color", type=str, default="184,184,209,255")
    ap.add_argument("--obj-color", type=str,  default="200,225,204,255")
    args = ap.parse_args()

    hand = _ensure_trimesh(trimesh.load(args.hand, process=True))
    obj  = _ensure_trimesh(trimesh.load(args.object, process=True))

    # Optional: convert mm->m so viewer units are meters
    if args.mm:
        hand.apply_scale(0.001)
        obj.apply_scale(0.001)

    # If either mesh lacks vertex colors, paint a solid color
    hc = _parse_color(args.hand_color, [184,184,209,255])
    oc = _parse_color(args.obj_color,  [200,225,204,255])
    if not hand.visual.kind == 'vertex':
        hand.visual.vertex_colors = np.tile(hc, (len(hand.vertices), 1))
    if not obj.visual.kind == 'vertex':
        obj.visual.vertex_colors  = np.tile(oc, (len(obj.vertices), 1))

    # Center and normalize together (preserve relative pose)
    if not args.no_center or not args.no_unit_scale:
        # compute combined bounds
        all_pts = np.vstack([hand.vertices, obj.vertices])
        min_b, max_b = all_pts.min(0), all_pts.max(0)
        center = 0.5 * (min_b + max_b)
        extent = float((max_b - min_b).max())

        if not args.no_center:
            T = np.eye(4)
            T[:3, 3] = -center
            hand.apply_transform(T)
            obj.apply_transform(T)

        if not args.no_unit_scale and extent > 0:
            s = 1.0 / extent
            hand.apply_scale(s)
            obj.apply_scale(s)

    # Put both meshes in a Scene and export GLB
    scene = trimesh.Scene()
    scene.add_geometry(hand, node_name="hand")
    scene.add_geometry(obj,  node_name="object")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    # Export as binary GLB (compact, single file)
    glb_bytes = scene.export(file_type='glb')
    with open(args.out, "wb") as f:
        f.write(glb_bytes)

    print(f"Wrote {args.out} (load with <model-viewer src='models/{args.out.name}'>)")

if __name__ == "__main__":
    main()

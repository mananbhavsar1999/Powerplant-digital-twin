# Week 2 — Blender Build Order Checklist
**Steam Turbine-Generator Package with Auxiliaries**

Total budget: ~7 days. Work in this order — biggest/simplest shapes first,
detail items last. Each item lists rough geometry approach + time budget.

---

## Day 1 — Layout & Baseplate
- [ ] Set up scene scale (use metric, 1 Blender unit = 1 meter)
- [ ] Block in the **skid/baseplate** — simple flat box, ~4m x 2m, turbine-generator
      package sits on this (real plants mount the whole train on one steel base)
- [ ] Rough-place bounding boxes for all major equipment so you can check overall
      layout/spacing before detailing anything (boiler, turbine, generator,
      condenser, feed pump)
- **Time budget: 2-3 hrs**

## Day 2 — Core Vessels (simple primitives)
- [ ] **Boiler/steam drum** — horizontal cylinder + dished end caps, support legs
- [ ] **Condenser** — horizontal cylinder, slightly larger diameter, end covers
      with simple flange detail (ring of bolts can be a normal map, not geometry)
- [ ] **Lube oil tank** — simple rectangular tank with rounded top, sits at
      skid base level (real lube oil tanks are often gravity-drained)
- **Time budget: 3-4 hrs** — these are big, simple shapes, don't over-detail

## Day 3 — Turbine & Generator (the hero objects)
- [ ] **Turbine casing** — this is the visual centerpiece, spend the most time
      here: tapered cylindrical casing, inlet steam chest (box-ish bulge),
      exhaust flange to condenser, mounting feet
- [ ] **Turbine rotor** — MUST be a separate object (named `turbine_rotor`),
      sits inside casing, only needs to be roughly visible through any
      casing window/cutaway, or fully hidden — what matters is it's a
      separate rotating mesh for animation later
- [ ] **Generator** — cylindrical body with cooling fins (can use a simple
      array modifier for fins, don't model each one by hand), end caps,
      coupling to turbine shaft
- **Time budget: 4-5 hrs**

## Day 4 — Feedwater Pump & Piping Layout
- [ ] **Feedwater pump** — small cylindrical pump body + motor (box + cylinder
      combo), mounting base
- [ ] Lay out main steam piping path: boiler outlet → turbine inlet, turbine
      outlet → condenser, condenser outlet → feed pump → boiler inlet
      Use Blender curves + bevel (Add > Curve > Path, then Bevel Depth in
      Curve properties) — much faster than manually modeling pipe sections
- **Time budget: 3-4 hrs**

## Day 5 — Lube Oil & Control Oil Auxiliaries
- [ ] **Lube oil pump** — small pump + motor, mounted near oil tank
- [ ] **Lube oil cooler (PHE)** — rectangular finned block (plate heat
      exchangers are visually distinctive — flat rectangular box with
      visible plate-pack lines, can be a texture/normal map detail)
- [ ] **Duplex oil filter** — two small cylindrical canisters side by side
      with a shared header — this duplex detail is a nice realism touch
- [ ] **Control oil skid** — can be simplified to a small combined block
      (pump + accumulator bottle + valve manifold) rather than fully
      detailing each sub-component — don't over-invest here
- [ ] Route oil piping (smaller diameter curves) from tank → pump → filter
      → cooler → turbine bearings, and back to tank
- **Time budget: 3-4 hrs**

## Day 6 — Materials
- [ ] Apply PBR materials using Principled BSDF:
  - Steel/metal casings: metallic ~0.8, roughness ~0.3-0.4
  - Insulated pipes (steam lines): matte cladding look, metallic ~0.2,
    roughness ~0.6, slight color variation
  - Oil system components: darker grey, more reflective (oil-wetted look)
  - Add a subtle "warning paint" version of key materials now (amber/red
    variants) — Three.js will swap to these on fault conditions later
- [ ] Name every object clearly and consistently (e.g. `turbine_rotor`,
      `boiler_body`, `lube_oil_pump`, `oil_cooler_phe`) — this matters a lot
      for targeting parts in Three.js animations
- **Time budget: 3 hrs**

## Day 7 — Export & Optimize
- [ ] Check total poly count (aim under ~50-80k triangles total for fast web load)
- [ ] Export as `.glb` (File > Export > glTF 2.0, format: glTF Binary)
- [ ] Run Draco compression (built into Blender's glTF exporter — enable
      "Compression" checkbox) to shrink file size further
- [ ] Test in https://gltf-viewer.donmccurdy.com/ — verify:
  - All objects appear correctly
  - Object names are intact (check the scene outliner in the viewer)
  - File size is under ~8-10 MB
- [ ] If size is too large: reduce texture resolution, check for duplicate
      geometry, use Decimate modifier on any overly dense meshes
- **Time budget: 2-3 hrs**

---

## Final Equipment Checklist
- [ ] Boiler / steam drum
- [ ] Turbine casing
- [ ] Turbine rotor (separate object)
- [ ] Generator
- [ ] Condenser
- [ ] Feedwater pump
- [ ] Lube oil tank
- [ ] Lube oil pump
- [ ] Lube oil cooler (PHE)
- [ ] Duplex oil filter
- [ ] Control oil skid (simplified)
- [ ] Main steam piping
- [ ] Oil system piping
- [ ] Common skid/baseplate

## Naming Convention (use consistently)
```
turbine_casing
turbine_rotor
generator_body
boiler_drum
condenser_shell
feedwater_pump
lube_oil_tank
lube_oil_pump
oil_cooler_phe
oil_filter_duplex
control_oil_skid
piping_steam_main
piping_oil_main
skid_baseplate
```
These exact names will be referenced directly in the Three.js code in Week 3,
so keep them consistent and avoid renaming later.

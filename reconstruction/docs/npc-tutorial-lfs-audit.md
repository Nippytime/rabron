# W1-D — verified NPC and tutorial LFS bundle audit

**Actually executed on the original owned-client LFS bytes:** 
https://github.com/Nippytime/rabron/actions/runs/43587524219

The original Git repository stores 133-byte pointers for both bundles.
This run first checked each pointer against the source ledger, selectively
fetched the original binary with Git LFS, and verified **UnityFS magic,
exact byte length, and full streamed SHA-256**. UnityPy 1.25.4 then
inventoried object kinds and numeric MonoBehaviour fields.

| Measured source | NPC bundle | Tutorial bundle |
| --- | ---: | ---: |
| Git LFS byte length | 98,896,651 | 84,166,120 |
| SHA-256 | aacec65903186775c8b834ba89cbbc0fea1419d857f14a0d95943732f12a0d69 | 56f1993ad49ac265c3268667557b0ec13c1c0f39fb7ada94ae4251e4328ac691 |
| MonoBehaviours parsed / total | **374 / 374** | **0 / 0** |
| Numeric records reporting field/depth truncation | 0 | 0 (no records) |
| MonoBehaviour parser errors | 0 | 0 |
| Max numeric fields / depth | 1,024 / 24 | 1,024 / 24 |
| AssetBundle objects | 1 | 1 |
| GameObjects | 7,386 | 0 |
| AnimationClips | 88 | 0 |
| Animator / AnimatorController / overrides | 50 / 5 / 6 | 0 |
| Avatars | 5 | 0 |
| SkinnedMeshRenderers | 311 | 0 |
| Meshes | 146 | 0 |
| Textures | 94 | **113** |
| Sprites | 0 | **113** |

The observed **374 NPC MonoBehaviours** contain 36 numeric fields matching
the summarizer's *combat* keywords and 568 matching its
*timing-and-world* keywords. This is only lexical classification:
samples include camera focus distance, an on-screen auto-fire rectangle,
and action timers. **No original NPC damage, weapon behavior, police AI,
loot, prices or authoritative backend rules have been verified.**
Most NPC MonoBehaviour names are empty or presentation-related, so
classifying all these values as gameplay tuning would be unsound.

The **tutorial bundle contains only 113 sprites and 113 textures** plus
one AssetBundle descriptor. Its zero MonoBehaviours is a real,
successfully verified inventory result—not a parse failure, and **not
proof that tutorial gameplay logic has been recovered**. That logic
must be sought in other bundles, IL2CPP methods, observations or
clean-room design.

## Coverage effect

- The number of tracked bundles remains **330**.
- Documented MonoBehaviour/object-type scans increase from **15 to 17**.
- Total successfully parsed MonoBehaviours across those scans increase
  from **9,107 to 9,481**.
- **313** other bundle paths remain without a documented scan in this
  ledger. Both previously pending NPC/tutorial LFS sources have now been
  inspected and removed from the pending list.
- The **26 unresolved historic field-limited** records from W1-C remain
  incomplete; this audit has not changed their status.
- Matching GameAssembly.dll, original game/server code, original
  authoritative balance formulas and redistribution rights are not
  established.

## Provenance and reproducibility

Original LFS OIDs, byte lengths, scans and source-kind counts live in
\`reconstruction/data/extraction_coverage.json\`. The GitHub Actions run
retains two short-lived numeric-only \`npc-tutorial-source-evidence-*\`
artifacts containing the registered SHA/size verifier result, the raw
MonoBehaviour path/field inventory, and a bounded candidate summary.
Neither meshes, textures, sprites nor other original media were
exported into the independent Unity prototype.

To run on a copy of the repository with Git LFS available, from its
root (example shown for NPC):

~~~bash
asset=StreamingAssets/aa/StandaloneWindows64/npc_assets_all.bundle
python -m reconstruction.tools.verify_priority_lfs "$asset" \
  --phase pointer --ledger reconstruction/data/extraction_coverage.json
git lfs pull --include="$asset" --exclude=""
git lfs checkout "$asset"
python -m reconstruction.tools.verify_priority_lfs "$asset" \
  --phase bytes --ledger reconstruction/data/extraction_coverage.json
python reconstruction/tools/extract_unity_bundle.py "$asset" \
  --max-fields 1024 --max-depth 24 \
  --expect-sha256 aacec65903186775c8b834ba89cbbc0fea1419d857f14a0d69 \
  --output /tmp/npc-numeric-evidence.json
~~~

The two-source workflow performs the same verification for both sources.
\`complete_numeric_extraction=true\` refers **only** to examined numeric
MonoBehaviour fields within the explicit limits. In the tutorial case
it is vacuously true because no MonoBehaviours exist: there are no
tutorial numerical rules to extract from that particular bundle.

Next waterfall W1 source targets should prioritize serialized configs
and MonoScript IDs in the remaining 313 bundles and organize observed
player progression/tutorial behavior, without inventing source facts.
Real Unity Editor/Play Mode/Windows EXE validation is still **not run**
under control issue #9.

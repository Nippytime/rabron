# W1-J: three source-verified large original weapon UnityFS inventories

**Measured original-source CI:** https://github.com/Nippytime/rabron/actions/runs/43629339564

The exact three original `StreamingAssets/aa/StandaloneWindows64/` non-LFS
weapon bundles in `reconstruction/data/large_weapon_source_targets.json`
were independently retrieved in three bounded single-source GitHub Actions
jobs. The existing read-only UnityPy 1.25.4 scanner checked each original
Git blob ID, actual byte count, UnityFS magic and computed SHA-256.
Per-file-scoped Unity MonoBehaviour identities and bounded numeric scans
used **2,048 fields per record and depth 32**. No original mesh, image,
audio, executable or script content was exported.

| Original bundle | Verified bytes | Parsed/total MonoBehaviours | Combat keyword field matches | Measured SHA-256 |
| --- | ---: | ---: | ---: | --- |
| `weapon-cb45_assets_all.bundle` | 39,106,539 | 56 / 56 | 132 | `f10f3735a137f78d7ae7a96f07d32b515d26bf6cb342c82bdea37a1ee5d084d0` |
| `weapon-drm14_assets_all.bundle` | 51,627,736 | 78 / 78 | 198 | `6bacbbe3c66950cea665dd018f29fd57dd24a48b2634b24012da4c3660a69c39` |
| `weapon-harris500_assets_all.bundle` | 44,766,652 | 112 / 112 | 264 | `9d5d4458a5087f22123968f4b153bc5a35cadaa7f1a0412f4a514342f79f6314` |
| **Total** | **135,500,927** | **246 / 246** | **594** | Per-original hashes above |

All three original files yielded a **bounded complete** MonoBehaviour
numeric pass (zero unparsed objects, zero field/depth truncation).
Other keyword category totals (economy, progression, timing/world) were
zero for this selected batch. These are heuristic field-path counts, not
verified original weapon damage, recoil, accuracy, networking, projectile
physics, ammunition effects, animation fidelity or server authority.

Measured Git SHA-1 IDs, SHA-256s, original sizes, object-type counts,
parsed totals, limits, numeric completion status and candidate counts
are committed in `reconstruction/data/extraction_coverage.json`.
Individual scoped Unity object path identities and bounded candidate
examples remain metadata-only CI artifacts. Later current-head CI
reruns all three originals against the committed records and fails
on source or numeric inventory drift rather than treating an empty
unscanned target set as green.

## Updated recovery boundary

- Documented original UnityFS sources: **164 of 330**.
- Parsed MonoBehaviours: **80,180**. The parsed count does not mean
  original source code, network logic or full scene graphs are recovered.
- **166** original bundle paths still lack a documented scan:
  **140** medium non-LFS, **6** large non-LFS, and **20** pending LFS sources.
- **35** known numeric field-cap records remain unresolved:
  26 historical, 7 localization, 1 W1-H realm and 1 W1-I settlement
  (65 historic raw capped observations, 30 targeted historical resolutions).
- Matching GameAssembly.dll, original IL2CPP method bodies, server code,
  source-authoritative gameplay/economy formulas and rights to reuse
  original game media remain **unverified or missing**.
- Actual Unity 6000.3 Editor import, Play Mode, Windows EXE runtime smoke,
  and whole-game W1–W8 acceptance have **not** been executed.

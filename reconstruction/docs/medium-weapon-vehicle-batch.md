# W1-G — actual medium weapon and vehicle UnityFS source inventory

**Verified source run:** https://github.com/Nippytime/rabron/actions/runs/43592228322

Ten exact original non-LFS Git-tracked sources were read from an authenticated
GitHub recursive tree pinned to the checked-out Git tree SHA; 72,243,123
source bytes were selectively sparse-checked-out across four jobs. Each source
was verified against original Git blob SHA-1, byte size, UnityFS signature and
independent SHA-256. UnityPy 1.25.4 read-only metadata extraction used
2,048 numeric fields and max depth 32 per MonoBehaviour, keeping path IDs
and explicit parse gaps. Results were reconciled against the exact ten-path
manifest in `reconstruction/data/medium_source_targets.json`.

| Original medium bundle | Original bytes | Parsed/total MonoBehaviours | Combat/timing keyword candidates | Measured SHA-256 |
| --- | ---: | ---: | ---: | --- |
| `vehicle-car-buletti_soltempra_assets_all.bundle` | 1,967,269 | 328 / 328 | 0 / 182 | `9b8d93d9aa38f8381166439637662bd609467d6ae71f19cb45f3615899515ab7` |
| `vehicle-car-fukurou_spark_assets_all.bundle` | 10,904,845 | 232 / 232 | 0 / 104 | `0cee481faff38f7f4470cea08eb4f1fbee991d1007c4c1b39d9d06e9a722cc30` |
| `vehicle-car-fukurou_tensa_assets_all.bundle` | 4,677,936 | 364 / 364 | 0 / 182 | `6deddd782ad2d977dbce28be744525d7aa0d8e59903f7a77c3ecabb42479f92f` |
| `vehicle-car-longhorn_titan_assets_all.bundle` | 4,803,693 | 456 / 456 | 0 / 156 | `44c610437fc99e65b54af2e7d6bd15ebb3d96b1203fd09a394761cce2fdcd934` |
| `vehicle-car-longhorn_wild_assets_all.bundle` | 5,766,267 | 390 / 390 | 0 / 182 | `2615f0b4e2b1a71326b1779c6d875c6b4bd65e39f77447217d3e0156ff63b0d7` |
| `vehicle-car-royal_e_assets_all.bundle` | 3,277,703 | 434 / 434 | 0 / 182 | `4857196f8ddc4845b1e7bb25d443b4554296b02cefa7e8570e87128494e0afaf` |
| `vehicle-car-royal_j_assets_all.bundle` | 3,603,277 | 360 / 360 | 0 / 156 | `800215ad9e9b1063bf0b36e7de2b3b52197354d10da9b8540588f94ca4b24bba` |
| `weapon-dp9_assets_all.bundle` | 9,129,948 | 60 / 60 | 176 / 0 | `88f1ed59f6f3d838e7f9fb5e0ee11a316959bf8e56060be59ee0a154d283b5fd` |
| `weapon-ordr12_assets_all.bundle` | 13,403,552 | 56 / 56 | 132 / 0 | `c668c521e0e19404903be2baf40ded78c80ad65b0f0e23eafab132317f43ec0c` |
| `weapon-starh_assets_all.bundle` | 14,708,633 | 53 / 53 | 132 / 0 | `80cc1eb7a1abdef8e35ce73e7044b053d5c18505c6ed847110b7408ab0694233` |
| **Totals** | **72,243,123** | **2,733 / 2,733** | **440 / 1,144** | Individual source hashes above |

All ten sources completed bounded MonoBehaviour numeric scans with
**zero unparsed records and zero reported field/depth truncation**. The
object-type counts, measured identifiers, tool limits, SHA-256 and explicit
completion flags are in `reconstruction/data/extraction_coverage.json`.
Additional per-object IDs and bounded candidate samples are retained as
short-lived GitHub Actions artifacts (not original game binaries).

**Interpretation limit:** These numbers are *keyword-matched serialized
client metadata*. Counts are not server-approved gameplay rules. Car
asset names do not establish horsepower, torque, cargo capacity, fuel,
vehicle damage or traffic behavior. Weapon paths do not establish
authoritative hit registration, recoil trajectories, spread, DPS, fire rate
or network anti-cheat rules. This pass recovered **no original IL2CPP
methods**, original server economy/code, meshes, textures or usable sound
files. No source numeric values were injected into gameplay code.

## Source inventory delta and next work

- Scanned/source-documented paths: **142 → 152 of 330**.
- Parsed MonoBehaviours: **14,855 → 17,588**.
- Remaining unscanned: **178**, including **146** medium non-LFS,
  12 large non-LFS and 20 unresolved LFS pointer sources.
- Unresolved bounded numeric field-capped records remain **33**:
  26 historical and 7 localization from W1-F.
- A source recheck mode reruns all ten original medium paths if and only
  if the full W1-G measured ledger is present. It fails if any bytes,
  source identifiers, parsed counts or candidate counts drift;
  a zero-source matrix cannot pass.
- **Not run:** Unity 6000.3 Editor import, real Play Mode, Windows EXE
  validation or full game acceptance. Issue #9 remains open; W1
  source-evidence gate remains incomplete.

Historic source scans of other medium and LFS bundles must not be
double-counted. This is W1 evidence recovery, not completion of W2/W3,
multiplayer, production visuals or original-mechanics parity.

# W1-AH — Original shared-props and Wwise battle LFS source audit

**Measured original-byte run:** [GitHub Actions #43660706725](https://github.com/Nippytime/rabron/actions/runs/43660706725), against
PR #88 at `dc718ba3dac86b5aa43e073f7dd105db97028bab`.
**Plan mode:** `new`; `documented_before=320`, `tracked_bundles=330`.
**Reconciliation:** [measured-ledger artifact #14139802061](https://github.com/Nippytime/rabron/actions/runs/43660706725/artifacts/14139802061)
reported `documented_after=322`, `new_documented=2`,
`source_reverified=0`, `unscanned_after=8`, with no attempted
source marked absent/unparseable. This is *source inventory coverage*,
not complete gameplay or full numeric-field verification.

## Actual measured source identities

| Pinned UnityFS original source | Git LFS SHA-256/OID | Actual original bytes | Typed objects | MonoBehaviours parsed / total | Numeric outcome |
| --- | --- | ---: | ---: | ---: | --- |
| `shared-environment-props_assets_all.bundle` | `4f6060da626a580259fd7f1eec148693e0b727e6f52966afa56fd692224671f5` | 114,599,702 | **5,780** | **0/0** | No MonoBehaviour fields present; bounded pass complete |
| `wwisedata_windows_battle_assets_all.bundle` | `178aa3dfc5353830250498240b1822e31f825baa7b0bef6925d1dd718fde8c59` | 107,969,136 | **2** | **0/1** | **One oversized MonoBehaviour explicitly unparsed**, so numeric pass **incomplete** |

Original Git pointer blob SHA-1s: shared props
`cf10acf22628deb01f1c30aff6b435e1f3646ede`;
Wwise battle `127dca708caaabc64ccf0f8548112a0a3df2b766`.
The Actions workers checked each pointer, fetched exactly its original LFS
bytes, validated original UnityFS signature/byte length/SHA-256, ran
read-only UnityPy 1.25.4 metadata passes and published real source JSON.
Both were reconciled using the repository's strict two-original identity
and typed-object/MonoBehaviour accounting rules.

## Unity object-type accounting

- Shared props: `AssetBundle=1`, `GameObject=1,149`, `Transform=1,149`,
  `Mesh=901`, `MeshFilter=899`, `MeshRenderer=899`, `Texture2D=444`,
  `LODGroup=171`, `Material=167`; total **5,780**, **0** MonoBehaviours,
  **0** unparsed records and **0** numeric caps.
- Wwise battle: `AssetBundle=1`, `MonoBehaviour=1`; total **2** Unity
  objects. Original MonoBehaviour serialized object at path ID
  `4287568105139389377` declares **116,892,416 bytes**. Reading its
  entire typetree previously exhausted the GitHub-hosted runner at
  ~15 GB resident memory. The Wwise-specific scanner now records the
  exact object header, detects that the serialized object exceeds the
  **8 MiB parse budget**, and explicitly marks the MonoBehaviour
  **unparsed** as `WwiseMonoObjectBudgetExceeded`. This limitation was
  confirmed in [the successful Wwise source job](https://github.com/Nippytime/rabron/actions/runs/43660706725/job/132649200855).
  It does **not** claim that object's unknown numeric fields or
  authoritative audio/gameplay data were recovered.
- Both sources reported **zero measured numeric keyword candidates** for
  `economy`, `combat`, `progression` and `timing_and_world`.
  For Wwise, this is **not evidence of zero actual numeric fields**:
  its only MonoBehaviour has not been parsed. There are **0** newly
  recorded numeric field caps, but **1** Wwise unparsed record. Neither
  is an authoritative server/game formula.

## Coverage and remaining boundaries

These two original sources advance the **documented original-source
inventory** from **320/330** to **322/330**. Eight tracked source
bundles remain unscanned. The previously documented **44 unresolved
numeric caps** are not fixed by this result. The Wwise media blob still
contains **one explicitly unparsed MonoBehaviour**, outside those
field-limit caps.

The original Wwise objects, audio media, missing IL2CPP implementation
bodies, unavailable authoritative server logic, and original media
redistribution rights remain **not recovered / not resolved**.
No source code, textures or sound payloads were exported.

## Final acceptance still pending

1. Commit the **actual** two-source metadata records into
   `reconstruction/data/extraction_coverage.json`, with the truthful
   Wwise `bounded_numeric_scan_complete=false` / `unparsed_records=1`.
2. Rerun the **original binary** W1-AH workflow on that updated PR head
   in `recheck` mode for **both** exact original source files. Require
   a successful nonempty 2/2 reconciliation with
   `source_reverified=2` and `new_documented=0`.
3. Require every other applicable current-head GitHub workflow/job
   nonempty and green, then verify unchanged PR head/base before merging.
   Verify the postmerge `dev` Python job and update control issue #32.
4. Do not claim W1 complete, Numeric Pass fully complete, playable Unity
   Editor/Windows EXE acceptance, or original server formulas. Retain
   W1-AI #89 as the next planned source-extraction item.

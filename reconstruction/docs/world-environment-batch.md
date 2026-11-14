# W1-H: measured world/environment UnityFS original source scans

**Verified source CI:** https://github.com/Nippytime/rabron/actions/runs/43627300176

Six selected medium (1 MiB–under 20 MiB) original non-LFS bundles from
`reconstruction/data/world_source_targets.json` were actually read and
inventoried in three bounded batches, using the shared Git-tree-pinned
source verifier and UnityPy 1.25.4 at **2,048 numeric fields / depth 32**.
Each exact source's original Git SHA-1, size, UnityFS signature and measured
SHA-256 were checked. Only metadata was retained, not original game media.

| Original bundle | Source bytes | Parsed/total MonoBehaviours | Numeric field caps | Combat/timing keyword matches | Measured SHA-256 |
| --- | ---: | ---: | ---: | ---: | --- |
| `environment-interactive_assets_all.bundle` | 18,259,250 | 655 / 655 | 0 | 0 / 2 | `64720ae44bb90e06da8fe8047bca41179dbe1a59361aac3a7493504c64425914` |
| `environment_assets_all.bundle` | 1,446,102 | 63 / 63 | 0 | 0 / 7 | `40cba35fb2a5c11c95e7183409457455b9407a53bf0ee02afa9ce999bf91cec2` |
| `shared-environment-city_assets_all.bundle` | 10,336,109 | 0 / 0 | 0 | 0 / 0 | `98356513abd9d35be6a29707aa3dd0e7b8041c2074be27e52e2c2a4d0a40b870` |
| `space-battle_assets_all.bundle` | 12,559,065 | 52,685 / 52,685 | 0 | 15 / 17,008 | `cb65821a2b400da8135efae72d5ca2f9b2aa486b8f12aa0f656d4b4871e010be` |
| `space-mainmenu_scenes_all.bundle` | 9,412,936 | 187 / 187 | 0 | 1 / 142 | `bcc1b020db54368306013c7efed82e768eccecebe6cba77310e5c3a029c08825` |
| `space-realm_assets_all.bundle` | 2,293,350 | 7,605 / 7,605 | 1 | 0 / 2,294 | `01a4ac3bb238208813e2db56899be3b6c072e6687da94df4bacb2595a7e82099` |
| **Total** | **54,306,812** | **61,195 / 61,195** | **1** | **16 / 19,453** | Source hashes above |

**Additional keyword matches:** economy 36; progression 61. All category
counts come from serialized-client field-path string matching, **not
proven gameplay rules**. The `space-battle` source contributed 52,685
MonoBehaviour records; the shared-city environment bundle contained
zero MonoBehaviours, while still being a verified source inventory of
other Unity object types.

**Explicit incomplete numeric source:** the `space-realm_assets_all.bundle`
source had **1 field-limit-capped MonoBehaviour** (source path ID
`-7117516320574321439`). It is included among 7,605 parsed typetrees
but its numeric field extraction is **partial**. No source in this batch
reported unparsed MonoBehaviour typetrees. These bounded passes are
not full game source recovery, nor full Unity content/mesh/scene export.

## Durable ledger and unrecovered scope

- `reconstruction/data/extraction_coverage.json` now holds **158/330**
  documented original bundle passes, with **78,783** parsed MonoBehaviours.
- **172 original bundle paths** still lack a documented source pass:
  **140 medium non-LFS**, **12 large non-LFS**, and **20 pending LFS
  sources**.
- **34 unresolved numeric-cap records** remain (26 historical, 7 new
  W1-F localization, 1 W1-H realm). The ledger's historic reported cap
  count is 64, including 30 previously resolved by targeted rescans.
- All six SHA-256s, original Git object IDs, byte sizes, object types,
  bounded counts, caps and candidate category counts are source-anchored
  in the machine-readable ledger; individual MonoBehaviour path IDs
  and partiality reasons are in the run's metadata-only batch artifacts.
- On later PR heads the same six sources are **rechecked** against
  original byte identities and committed bounded inventory. Any
  missing target or data drift fails rather than producing an empty
  "all good" job.

**Still not recovered:** original matching IL2CPP method bodies,
GameAssembly.dll, server authority, proven combat/vehicle/economy
coefficients, asset redistribution permission, gameplay observation
coverage. Unity 6000.3 Editor import, Play Mode and Windows EXE manual
acceptance have **not** been run (issue #9). W1 evidence exit gate and
future full-game waterfall phases remain unfulfilled.

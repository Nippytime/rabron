# W1-AN — original city-scene five numeric-cap object identity audit

## Evidence
- First source-only [W1-AN run #43676991456](https://github.com/Nippytime/rabron/actions/runs/43676991456) completed **three nonempty successful jobs**: exact original Git pointer and ledger plan, full downloaded UnityFS scan, and strict five-object reconciliation. The original evidence artifact is `city-cap-identities-measured` (GitHub Actions artifact **14145734445**); the 1,889-byte JSON evidence entry's SHA-256 is `cec47eac7a3ec83858eb163befd12213e23dbe0be6447d7ccb526a5caf1d9456`.
- Integrated original source fingerprint: Git LFS SHA-256 `5c06c4527fa48871b842e76d8dab5e37f9fde91da9b99a806270a763becadc7f`, exact **549,566,135 bytes**. The pointer SHA-1 `c73e7b84edc6b4e73001923054ff3a29bd540393` was independently checked before the original LFS download.
- The same bounded streaming reader preserved source scope and scene indexes, and the original 2,048 numeric field / depth-32 budget. It reconciled **366,174 typed Unity objects**, **14,467 MonoBehaviours attempted and parsed**, **exactly five capped**, and **zero newly unparsed**.
- Report is in `reconstruction/data/city_scene_numeric_cap_identities.json` with only object identifiers and truncation metadata. It deliberately excludes original numeric values, object text bodies, scene geometry, media and proprietary assets.

## Five explicitly capped original object identities

| Serialized file | Unity path ID | Object name | Visible numeric fields | Truncation cause |
| --- | ---: | --- | ---: | --- |
| `CAB-198a5be741d1a7bef84198e0c583d1cf` | `344196` | unnamed | 2,048 | `field_limit` |
| `CAB-198a5be741d1a7bef84198e0c583d1cf` | `344216` | unnamed | 2,048 | `field_limit` |
| `CAB-198a5be741d1a7bef84198e0c583d1cf` | `344248` | unnamed | 2,048 | `field_limit` |
| `CAB-198a5be741d1a7bef84198e0c583d1cf` | `344310` | unnamed | 2,048 | `field_limit` |
| `CAB-198a5be741d1a7bef84198e0c583d1cf.sharedAssets` | `7968` | `WaterQuadTreeData` | 2,048 | `field_limit` |

**Scope and limitations:** All five remain numeric-capped and unrecovered, not inferred zero and not confirmed original gameplay formulas. Four missing names are truly blank in the source metadata and must not be guessed. `WaterQuadTreeData` is a source name, not authority on original server logic. Unique Unity identities require both `serialized_file` and `path_id`; a bare integer alone is insufficient. A subsequent source-scoped adaptive retry must separately prove any newly recovered fields and maintain bounded memory.

## Integration gate

This measured artifact is committed **only to the work branch** initially. Require a fresh latest-head original binary recheck to reproduce the same five identities (mode `recheck`, reverified 5/5), passing all actual current-head Actions workflows, checks and nonempty jobs; then gated squash merge and exact-merge `dev` Python. Original source-path ledger stays **330/330**; global unresolved numeric caps stay **325**, and the two oversized Wwise unparsed objects remain.

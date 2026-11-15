# W1-AO — bounded selected city numeric-field retry, first-original evidence

Source of evidence: [full original-byte GitHub Actions run #43677848887](https://github.com/Nippytime/rabron/actions/runs/43677848887), **3/3 nonempty jobs completed success** (plan, strict full-original download/scan, reconciliation). Original 549,566,135-byte UnityFS verified against Git pointer SHA-1 `c73e7b84edc6b4e73001923054ff3a29bd540393` and original SHA-256 `5c06c4527fa48871b842e76d8dab5e37f9fde91da9b99a806270a763becadc7f`. Original measured `city-targeted-numeric-retry-measured` artifact **14147291601**: 5,018-byte metadata-only JSON SHA-256 `fa675a5d55af58b1ff05007ad9efb5cbaa2b60d0fd8f0ba1bbf78e3fbb6018c8`.

## Strict original selected-source results

All five identities reproduced their original **2,048-field/depth-32 `field_limit`**, were then rescanned only at **8,192-field/depth-32**, and **all five required an individually bounded adaptive 16,384-field/depth-48 retry**. Each retry preserved unique serialized-file/path-ID identity; no additional object selected, no source SHA drift, no unparsed object. Metadata-only record: `reconstruction/data/city_scene_targeted_numeric_retry.json`, with numeric *path names/digests* and bounded samples, **never numeric values or media**.

| Serialized file | Path ID | Outcome | Observed numeric fields | Remaining cause |
| --- | --- | --- | ---: | --- |
| `CAB-198a5be741d1a7bef84198e0c583d1cf` | `344196` | Still capped | 16,384 | `field_limit` (renderer references) |
| Same | `344216` | Resolved **for this selected numeric object** | 11,824 | None (AkEvents references) |
| Same | `344248` | Still capped | 16,384 | `field_limit` (mesh renderer references) |
| Same | `344310` | Resolved **for this selected numeric object** | 10,863 | None (lightmap renderer indices) |
| `CAB-198a5be741d1a7bef84198e0c583d1cf.sharedAssets` | `7968` (`WaterQuadTreeData`) | Still capped | 16,384 | `field_limit` (water quadtree nodes) |

**Result:** **2 selected objects resolved**, **3 still field capped**, **0 unparsed**. The `resolved` label applies **only to the bounded numeric traversal for these exact source-scoped client objects**, *not* to recovered server formulas or game mechanics. Object names and field categories are not authoritative gameplay balance. Four original names are blank. The three remaining caps may contain additional original numeric values and must stay incomplete.

The authoritative original scan's historical source cap count stays **355** globally, with **5 initial city caps** conserved as original evidence. Targeted `resolved_count=2, unresolved_count=3` reduces the **overall unresolved historical-accounting total from 325 to 323**, while preserving 330/330 original source paths, 143,131 parsed MonoBehaviours and the two separate oversized unparsed Wwise MonoBehaviours. This does not claim full original source-code, authoritativeness, media rights, Unity Editor/Play Mode or Windows EXE acceptance.

**Integration gate:** These results are initially proposed on the work branch only. Require a fresh full-original exact-current-head `mode=recheck`, strict identity/path-digest/count equality, all current-head nonempty Actions and Python checks green, guarded squash merge, exact-merge `dev` CI, child issue and control update before counting two resolved objects as integrated.

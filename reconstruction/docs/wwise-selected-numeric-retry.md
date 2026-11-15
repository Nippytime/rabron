# W1-AQ — bounded selected Wwise numeric retry: original source evidence

## Actual first-original proof

First [Actions run #43681605464](https://github.com/Nippytime/rabron/actions/runs/43681605464) completed all three real jobs successfully: source pointer and tests, downloaded original UnityFS bounded scan, and strict three-ID reconciliation. Summary: mode=new, resolved=0, unresolved=3, verified_identities=3, reverified=0, full_bundle_numeric_extraction_complete=false.

Source StreamingAssets/aa/StandaloneWindows64/wwisedata_windows_assets_all.bundle: exact 170,634,407 bytes; original SHA-256 d84888fe94f74b5cb817749abbcb1af59225300523ad9a1a14e01f475e08fb35; original LFS pointer Git SHA-1 40324cc5a4281d764319e2291e9fb7c142208c57. Existing Wwise stream and 8 MiB per-MonoBehaviour memory ceiling unchanged.

First measured artifact wwise-selected-numeric-retry-measured ID 14148204197 contains a 2,768-byte JSON, SHA-256 11a9f32db0134a0a42c7031b03c3f12b77fd03cdb0e24bb2d2760d12543d2428, Git blob SHA-1 dee123cec38ce47b2d58478a90ee4046b46b95b0. Its byte-identical metadata-only content is committed as reconstruction/data/wwise_selected_numeric_retry.json. No original numeric values, Wwise media or decompiled object bodies were exported.

## Three independently selected results

All three objects are in serialized file CAB-0d2ba6020dca38a3a92a5458383d263a. Each reproduced an original field_limit at 2,048 fields/depth32 and identical original first-field-path digest, then was scanned at 8,192/depth32 and 16,384/depth48. All three remain explicitly incomplete.

| Original Unity path ID | Result at 16,384 fields | Cause |
| --- | --- | --- |
| -9215429395481605246 | still_capped | field_limit |
| -6697251573783040 | still_capped | field_limit |
| 9197897462607697745 | still_capped | field_limit |

All three have observed 16,384 numeric paths and identical bounded field-name digest c6194bbcd23fa7f03a36a52f689a5a803388ab69d6780821cefe4d47f574265a. The first eight sorted samples are $.RawData[0] and $.RawData[10000] through $.RawData[10006]. This is evidence of the visible field-path structure only. It does NOT establish that original numeric values, hidden fields, data beyond the cap, or the other 271 Wwise capped objects are identical. RawData from an audio-source bundle is not a gameplay/server rule.

**Conservation:** zero of three selected caps resolved, 271 unselected Wwise original caps untouched. Integrated historical 355 caps / 323 unresolved under targeted recovery accounting remain unchanged, as do 330/330 source paths, 143,131 parsed MonoBehaviours, and two globally unparsed Wwise objects. Full numeric/game reconstruction incomplete.

## Integration gate

First measured evidence is initially on the work branch. Require a fresh exact-head SHA-verified full-original mode=recheck reproducing all three statuses, field counts and field-path hashes; all nonempty Actions workflows/checks/jobs success; guarded squash merge to dev; exact-merge Python CI; close #109 and update parent #3/control #32. No scope expansion, media export or false resolution.

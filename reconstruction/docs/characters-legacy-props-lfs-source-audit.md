# W1-AJ original shared-character and legacy environment-props Git LFS verification

**Source-integrity status:** These are **measured original Git LFS UnityFS bytes**, not Git pointer text, fake records or recovered game/server code. First full-original source run: [W1-AJ Actions #43670816316](https://github.com/Nippytime/rabron/actions/runs/43670816316), **plan + both original source workers + strict reconcile, 4/4 real jobs success**.

## Exact original source inventory

| Original source | Declared, verified original bytes | Original Git blob SHA-1 | Original LFS SHA-256 / measured binary SHA-256 | Typed Unity objects | MonoBehaviours | Numeric cap/unparsed |
| --- | ---: | --- | --- | ---: | ---: | --- |
| `shared-characters_assets_all.bundle` | 164,119,824 | `9bdba42ebe861b6fe666f38a5caf7bf6b9ea6b77` | `68048c1c9005a267508c3820be20c33bd702df926dd9121dc4a1265a9a38ded9` | **1,122** | **0** | **0 / 0** |
| `environment-props-legacy_assets_all.bundle` | 183,967,345 | `574f5ca4be39e2253fda58b53a48cac2c9e6741e` | `563a4fa9ef206103bfbcd2f33995b6964d9d268501762ce7df1a62fe32709e19` | **622** | **0** | **0 / 0** |
| **Total newly verified** | **348,087,169** | | | **1,744** | **0** | **0 / 0** |

Both source workers validated exact Git pointer provenance before selective LFS download, original full UnityFS magic, size and SHA-256 after download, then read-only pinned UnityPy **1.25.4** metadata scan at **2,048 numeric fields/depth 32**. Zero MonoBehaviours is a true measured result, **not** missing metadata or permission to redistribute assets.

### Original object-type details
- **Shared characters:** Animator 2; AssetBundle 1; Avatar 2; GameObject 340; LODGroup 1; Material 32; Mesh 178; MeshFilter 40; MeshRenderer 40; SkinnedMeshRenderer 41; Texture2D 105; Transform 340. Total: **1,122**.
- **Legacy environment props:** AssetBundle 1; Material 217; Texture2D 404. Total: **622**.
- No extracted numeric gameplay candidates and no newly capped or unparsed MonoBehaviours. Client presentation metadata does **not** prove authoritative formulas, animation source code, server behavior, legal reusability or full game parity.

### Reconciliation / evidence ledger
- Original run [#43670816316](https://github.com/Nippytime/rabron/actions/runs/43670816316) measured `documented_before=324`, `documented_after=326`, `new_documented=2`, `source_reverified=0`, `unscanned_after=4`, `unparseable_attempts=[]`.
- Source artifacts: [shared-characters #14144291138](https://github.com/Nippytime/rabron/actions/runs/43670816316/artifacts/14144291138), [environment-props legacy #14144296855](https://github.com/Nippytime/rabron/actions/runs/43670816316/artifacts/14144296855), [strict measured ledger #14144405826](https://github.com/Nippytime/rabron/actions/runs/43670816316/artifacts/14144405826).
- Proposed branch evidence ledger **326/330** original sources, **4** remaining unscanned. Prior **128,363 parsed MonoBehaviours**, **76 total capped numeric records / 46 unresolved**, and **1** independent oversized Wwise unparsed MonoBehaviour are unchanged.
- **Not yet merged / complete:** Require a fresh exact-current-head full-original 2/2 `recheck` and every historical/Python/source workflow and job complete green before integration. Postmerge dev CI and issue/control update are separate gates.

### Remaining original source targets
`environment-materiallibrary-legacy_assets_all.bundle`, `location-city-standalone_scenes_city_standalone.unity.bundle`, `shared-environment-desert_assets_all.bundle` and `wwisedata_windows_assets_all.bundle`. These are Git LFS pointers only until independently verified and read-only scanned in separately gated work.

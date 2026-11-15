# W1-AL original Wwise Windows UnityFS LFS source audit

**Evidence:** [first original-byte source and strict single-source reconciliation #43673281268](https://github.com/Nippytime/rabron/actions/runs/43673281268) succeeded with three nonempty jobs (plan, original Wwise source scan, reconcile). The original binary was downloaded selectively, then verified against its exact Git LFS SHA-256, full **170,634,407-byte** size and UnityFS magic. The pointer Git SHA-1 was checked independently before download. This report documents **client serialized metadata only**, not code recovery or redistribution rights.

| Verified source | Pinned value |
| --- | --- |
| Original path | `StreamingAssets/aa/StandaloneWindows64/wwisedata_windows_assets_all.bundle` |
| Original Git pointer SHA-1 | `40324cc5a4281d764319e2291e9fb7c142208c57` |
| Full original LFS SHA-256 and measured binary SHA-256 | `d84888fe94f74b5cb817749abbcb1af59225300523ad9a1a14e01f475e08fb35` |
| Actual downloaded original bytes | **170,634,407** |
| Typed Unity objects | **276** (AssetBundle 1; MonoBehaviour 275) |
| MonoBehaviours parsed | **274 of 275** |
| Numeric field-capped records | **274** (bounded to 2,048 numeric fields, depth 32) |
| MonoBehaviour explicitly unparsed | **1** (object path ID `-8363773085191996504`, original serialized size **10,876,192 bytes**, above the per-object **8,388,608-byte** safety budget) |
| Numeric field candidates in combat/economy/progression/timing | **0 / 0 / 0 / 0** |
| Full bounded numeric scan complete | **No** |

The source scan used pinned UnityPy 1.25.4 and the existing bounded UnityFS streaming loader. Object headers were counted without extracting proprietary sound/media. **Parsed** here means the MonoBehaviour dictionary could be inspected; 274 parsed records still hit numeric-field limits, so their nested numeric content is **not complete**. The 10.9 MB source object was recorded as unparsed rather than skipped silently.

Strict first-original reconciliation: `documented_before=328`, `documented_after=329`, `new_documented=1`, `source_reverified=0`, `unscanned_after=1`, `unparseable_attempts=[]`. Source artifact [#14145107685](https://github.com/Nippytime/rabron/actions/runs/43673281268/artifacts/14145107685) and measured ledger artifact [#14145159049](https://github.com/Nippytime/rabron/actions/runs/43673281268/artifacts/14145159049) retain the original measured evidence.

Proposed branch original-source coverage becomes **329/330**; exactly one original city scene still unscanned and independently tracked under [issue #100](https://github.com/Nippytime/rabron/issues/100). Cumulative parsed MonoBehaviours become **128,664**. Cumulative numeric field cap records become **350**: **76 previous caps** (46 previously unresolved after targeted source-specific retries) and **274 new Wwise Windows caps**. Unresolved field caps under the existing accounting are therefore **320**, not zero. The prior separate Wwise-battle oversized unparsed MonoBehaviour also remains; combined explicit unparsed count is **2**.

**Integration gate pending:** These records are not yet in `dev`; require a fresh full-original exact-current-head singleton `recheck` with `source_reverified=1`, `new_documented=0`, full current-head Actions workflow and check success, unchanged refs, gated squash merge, postmerge `dev` Python CI, and issue/control updates. Neither source-path coverage nor byte verification proves authoritative game formulas, IL2CPP methods, legal asset reuse, Unity Editor/Play Mode acceptance or a Windows EXE.

# W1-AK original legacy material-library and shared-desert LFS source audit

**Evidence status:** exact actual Git LFS original UnityFS bytes measured; pointers are **not** source artifacts and no game source, original server rules or media rights are inferred. The first real original-byte run [W1-AK #43671682891](https://github.com/Nippytime/rabron/actions/runs/43671682891) completed **4/4 jobs success** (plan, two isolated source workers, strict reconcile).

| Original source | Exact SHA-256 (full source and pinned LFS OID) | Verified bytes | Typed Unity objects | MonoBehaviours parsed/total | Numeric caps / unparsed |
| --- | --- | ---: | ---: | ---: | ---: |
| `environment-materiallibrary-legacy_assets_all.bundle` | `38f2f9617e3deb1ea395a4ebd733692db812c6b4eff5ebb8b31878d3c1cafb80` | 239,172,482 | **1,304** | 0/0 | 0 / 0 |
| `shared-environment-desert_assets_all.bundle` | `4e2c4beb22bf1458e699fd917d7b300a9349253df99925fbf30284afe8da83b8` | 228,978,185 | **14,870** | 27/27 | 0 / 0 |
| **Combined** | | **468,150,667** | **16,174** | **27/27** | **0 / 0** |

- Original pointer Git blob SHA-1: material-library `b265856eb782bd13cc0edcfbd97eaa29fc778ed9`, desert `92a86d66dd7438a2327b1b48d8f22b8f961cd1a3`.
- Material library object classes: AssetBundle 1, Material **658**, Texture2D **645**.
- Shared desert object classes: AssetBundle 1, Cubemap 3, GameObject 2,899, LODGroup 55, LightingSettings 1, Material 150, Mesh **2,922**, MeshFilter 2,819, MeshRenderer 2,819, MonoBehaviour **27**, OcclusionCullingData 1, Texture2D 274, Transform 2,899.
- Desert numeric-candidate bounded fields: **combat 6, progression 2, timing/world 317, economy 0**. The bounded 2,048-field/depth-32 scan found **zero caps/unparsed** on these two sources. Metadata candidates are not actual original gameplay formulas.
- Exact Git pointer checked before selective Git LFS download; full-original SHA/bytes and UnityFS magic verified after download; read-only pinned UnityPy 1.25.4 type and MonoBehaviour scan.
- Run #43671682891 source artifacts: [material library #14144995287](https://github.com/Nippytime/rabron/actions/runs/43671682891/artifacts/14144995287), [desert #14144720977](https://github.com/Nippytime/rabron/actions/runs/43671682891/artifacts/14144720977), [measured ledger #14144129292](https://github.com/Nippytime/rabron/actions/runs/43671682891/artifacts/14144129292).
- Strict first-source reconciliation: `documented_before=326`, `documented_after=328`, `new_documented=2`, `source_reverified=0`, `unscanned_after=2`, `unparseable_attempts=[]`. Proposed branch ledger is **328/330**, with 2 still unscanned, **128,390** parsed MonoBehaviours, previous **76 historical capped records / 46 unresolved**, and **one separately unparsed Wwise MonoBehaviour**.

**Latest-head integration is NOT yet accepted:** after committing measured records, require fresh exact 2/2 full-original `recheck`, every current-head Python/historical/source check passed nonempty, unchanged refs, squash merge into `dev` and successful postmerge Python run.

Two remaining original sources: `location-city-standalone_scenes_city_standalone.unity.bundle` (549,566,135 original bytes) and `wwisedata_windows_assets_all.bundle` (170,634,407 original bytes). These require separate gated original-source work. No source asset redistribution, original game formulas, IL2CPP method bodies, authority or Unity Editor/Play Mode/Windows EXE acceptance is claimed.

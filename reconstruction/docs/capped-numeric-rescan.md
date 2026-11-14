# W1-C — targeted, provenance-checked historical overflow rescans

Issue #24. This is a **read-only client asset extraction** workflow, not
a recovered-gameplay implementation or proof of authoritative formulas.

## Why and how

The documented 15-bundle MonoBehaviour inventory includes **56**
historically field-capped objects across seven earlier bundles.
A bounded rescan does not need to re-export every scalar in thousands of
uncapped objects.

1. Read \`reconstruction/data/extraction_coverage.json\` for the exact
   historical SHA-256, MonoBehaviour count, and known cap count.
2. Obtain the identical original UnityFS bytes; selectively fetch the
   128.8 MB settlement LFS object. A pointer or mismatched SHA is a failure.
3. Reproduce the original 256/512/4096-field cap at traversal depth 16.
   Identify each previously **field-limited** Unity path ID from the
   serialized bytes. Compare the count to the existing measured evidence;
   discrepancy means investigate, not silently accept it.
4. Load and parse **only those path IDs** at max 8,192 numeric fields /
   depth 32. Retry remaining capped/failed IDs only once, at 16,384 fields /
   depth 48, to bound memory and artifact sizes.
5. Record each selected object's numeric field paths, path ID, remaining
   truncation reasons and actual parser failures. Never label unresolved
   or unparsed fields numeric zero.
6. Produce a small categorized summary and original-SHA-256-anchored
   research artifact for each bundle. \`targeted_numeric_extraction_complete\`
   refers only to recovered old caps; \`full_bundle_numeric_extraction_complete\`
   is **always false** for this selective workflow.
7. Review source-backed candidates before introducing any new independently
   authored economics, police, combat or vehicle tuning. Matching
   GameAssembly.dll and server data are still unavailable.

The expected seven historical overflow groups are:

| Source bundle | Historical numeric cap | Historically capped records |
| --- | ---: | ---: |
| scriptableobjects_assets_all.bundle | 4,096 | 25 |
| location-settlement-data_assets_all.bundle (LFS) | 512 | 12 |
| location-city-data_assets_all.bundle | 256 | 2 |
| location-hub-data_assets_all.bundle | 256 | 5 |
| location-sectorcenter-data_assets_all.bundle | 256 | 1 |
| location-settlement2-data_assets_all.bundle | 256 | 1 |
| inbuild_assets_all.bundle | 256 | 10 |
| **Total** | | **56** |

## Reproduce on a machine that has the original source bytes

~~~bash
python -m reconstruction.tools.rescan_capped_fields \
  StreamingAssets/aa/StandaloneWindows64/scriptableobjects_assets_all.bundle \
  --ledger reconstruction/data/extraction_coverage.json \
  --output /tmp/capped-records.json \
  --summary /tmp/capped-summary.json
~~~

The \`.github/workflows/rescan-capped-numerics.yml\` matrix runs all seven
with sparse checkout and a narrowly scoped Git LFS download for settlement.
It must **actually run and produce records** before recovered counts can be
reported. Passing unit tests alone does not prove any old caps were resolved.

## Scope and restrictions

- Extraction only traverses serialized **MonoBehaviour numeric fields**.
  It does not restore IL2CPP methods, original network/server formulas,
  non-MonoBehaviour data, mesh/texture/audio assets or licensed art rights.
- \`summarize_numeric_evidence.py\` uses keyword matches and excludes known
  pointer/animation patterns; candidate categories are heuristic.
- Unresolved field/depth caps remain explicitly flagged in results.
- No original assets are checked into authored Unity code; the research
  artifacts contain only numeric paths and small class/name metadata.
- Unity Editor/Play Mode and packaged Windows gameplay verification remain
  **not run** under separate issue #9.

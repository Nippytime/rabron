# Binary extraction — milestone 2

## Verified input

- Uploaded binary: StreamingAssets/aa/StandaloneWindows64/979ebaa5a17ed2834a47fa1373510580_monoscripts.bundle
- GitHub file SHA: 58a50f20b95d424e1edc1023b1326276b7732796
- Direct decoded header: UnityFS (bundle) / engine version **6000.3.18f1**
- Target first pass: StreamingAssets/aa/StandaloneWindows64/scriptableobjects_assets_all.bundle
- The uploaded IL2CPP metadata is present; matching GameAssembly.dll is missing.

## Read-only scanner

The scanner inventories object classes and extracts numeric MonoBehaviour fields
only when UnityPy successfully resolves a typetree. It exports no textures,
models, localized text assets or game executables.

Use a local Unity environment with Python 3.11 and UnityPy 1.25.4 (released
3 October 2026). From the repository root:

~~~bash
python -m pip install UnityPy==1.25.4
python reconstruction/tools/extract_unity_bundle.py \
  StreamingAssets/aa/StandaloneWindows64/scriptableobjects_assets_all.bundle \
  --output /tmp/scriptableobjects-index.json
~~~

With a 2000 MonoBehaviour inspection limit (the CI discovery configuration):

~~~bash
python reconstruction/tools/extract_unity_bundle.py \
  StreamingAssets/aa/StandaloneWindows64/scriptableobjects_assets_all.bundle \
  --max-behaviours 2000 \
  --output /tmp/scriptableobjects-index.json
~~~

The tool emits a SHA-256 of the source bundle, a count of Unity object types,
each examined MonoBehaviour path ID, numeric field paths and parsed values,
missing-typetree/error counts, field truncation flags, and a top-level
complete_numeric_extraction flag. A scan may succeed while the numeric data is
**incomplete**. Do not interpret a green CI result as proof that all game
balance fields have been recovered.

Its GitHub Actions workflow uses a sparse checkout to include only the
scriptableobjects bundle and authored scanner. JSON output is uploaded as a
short-lived artifact; no extracted game asset files are committed.

## Exhaustive inventory and depth-aware rescans (W1)

Every tracked Unity bundle should be inventoried **before** implementing
speculative missing systems. To generate a deterministic queue from the
Git tree (works even with sparse-checkout and Git LFS pointers):

~~~bash
python reconstruction/tools/plan_bundle_scans.py \
  --ref HEAD --min-tracked 330 \
  --output /tmp/bundle-scan-backlog.json
~~~

The planner combines every tracked .bundle filename with **15 documented
read-only MonoBehaviour passes** preserved in
reconstruction/data/extraction_coverage.json. The first nine scans have
56 reported numeric field cap occurrences. The six new scans (see
reconstruction/docs/gameplay-bundle-batch-1.md) parsed **1,320** more
MonoBehaviours at an 8,192-field/32-depth limit with zero reported
truncations, without recovering any authoritative gameplay formula. A pass without a reported field cap is still
**not automatically complete**: earlier scanner versions could skip nested
fields beyond their depth limit while reporting a false completeness flag.
The backlog prioritizes such rescans, real LFS fetches, and uninspected
bundle families. It never downloads binaries or labels extracted client
coefficients as server economics.

The scanner now marks records partial on **either** a per-record numeric
field cap **or** a nonempty nested subtree blocked by --max-depth. Both
limits are included in its output manifest. When selectively revisiting
relevant bundles, control the limits explicitly:

~~~bash
python reconstruction/tools/extract_unity_bundle.py \
  StreamingAssets/aa/StandaloneWindows64/scriptableobjects_assets_all.bundle \
  --max-fields 8192 --max-depth 32 \
  --output /tmp/scriptableobjects-deep-pass.json
~~~

This command is an example, not a claim that a new deep pass was executed.
Use a bounded amount of memory and CPU, retain checksums, and mark any
still-truncated fields as unknown. Keep authored code and research metadata
separate from the original proprietary files.

## Verified W1-C targeted overflow results

A new seven-source Actions run recovered the historical cap-limited path IDs
without re-exporting all MonoBehaviours:
https://github.com/Nippytime/rabron/actions/runs/43586244089 .

The original **56** field-limit records were all reproduced against the
source SHA-256. **30** are no longer capped at the documented 8,192-field /
32-depth pass plus bounded 16,384-field / 48-depth retry. **26** remain
truncated at the numeric field cap. This is explicitly **not** complete
bundle, IL2CPP or server formula extraction. The complete source-identified
path-ID result is recorded in
reconstruction/data/targeted_numeric_recovery.json and described in
reconstruction/docs/capped-numeric-rescan.md.



- UnityPy 1.25.4 docs: https://pypi.org/project/UnityPy/
- UnityPy API (parse_as_dict, peek_name):
  https://github.com/K0lb3/UnityPy
- Some MonoBehaviours omit typetrees. UnityPy's TypeTreeGenerator can
  reconstruct them with matching compiled Unity IL2CPP code and metadata,
  but this repo lacks the compiled GameAssembly.dll.
- Stored data may contain item identifiers, references, prices, timing, and
  arrays; **a number alone is not proof of the live server formula**.
  Formula reconstruction requires field meaning, version, validation against
  a running build, and confirmation of which values are server authoritative.
- Avoid bulk-distributing the proprietary asset data itself; keep research
  outputs limited to evidence needed to implement independently authored logic.

## Completion threshold

A useful next milestone report must state: bundles actually scanned, total
objects, MonoBehaviour parsed/unparsed counts, numeric field extraction
coverage, concrete known coefficients (with source paths), and unresolved
server-only formulas. Until then this remains an extraction **investigation**,
not a finished game reconstruction.

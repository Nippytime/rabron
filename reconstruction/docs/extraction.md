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

## Dependencies and limitations

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

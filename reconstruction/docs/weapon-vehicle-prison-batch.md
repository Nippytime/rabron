# W1-E — original weapon, vehicle and prison source inventory

**Actually executed using pinned UnityPy 1.25.4 in GitHub Actions:**
https://github.com/Nippytime/rabron/actions/runs/43588642907

The pipeline inventoried eight *previously undocumented* original, non-LFS
UnityFS bundles checked out individually from the Git tree. Each original
file's size and UnityFS header was verified; source SHA-256 was computed
from the real bytes and checked against both raw numeric and summarized
artifacts. Read-only extraction used max **2,048 numeric fields** per
MonoBehaviour and max **depth 32**, with typed parse failures and truncation
recorded, rather than silently reducing required counts.

| Original bundle (omit .bundle) | Bytes | Parsed/total MonoBehaviours | Combat-keyword fields | Timing/world-keyword fields | SHA-256 |
| --- | ---: | ---: | ---: | ---: | --- |
| weapons_assets_assets_content_equipment_weapons__sharedsources | 38,904 | 71/71 | 0 | 60 | ae26c904abc4601561b590cad540d2933b67a7144e3ac89a90ad12c772d9ddd5 |
| weapons_assets_assets_content_equipment_weapons__modules | 22,964,491 | 128/128 | 0 | 120 | 8ce9dbba8092891348647f7fff3996c41d08b526742e29a1b67c46470c405f98 |
| weapon-lmg_assets_all | 8,174,384 | 19/19 | 44 | 0 | d49480e7421e150ab75a7d14087b08cc56ecedc0febeded71a7bb5e3466fe3bf |
| weapon-lbr44_assets_all | 8,605,621 | 80/80 | 220 | 0 | dfd054278d5db84a94c6722df49f05209f7899294811476b03bb0cafa054f185 |
| vehicle-car-longhorn_guard_assets_all | 2,641,259 | 50/50 | 0 | 26 | db8bf4f9e989c3cf0747f22cca48a20555e0fcedb850bdd1129a0c0cba6ce598 |
| vehicle-car-longhorn_van_assets_all | 7,301,643 | 456/456 | 0 | 156 | b8771f2fe750f391265ef90fea747115d060a55da5c7e4d22d8b1687b0e14db9 |
| vehicle-car-longhorn_outrider_assets_all | 2,956,041 | 50/50 | 0 | 26 | 9e835c81457bc62d855a64ff6a92e625cf857d589c98900aa800e5b7bc053833 |
| location-prison-standalone_scenes_all | 41,145,162 | 248/248 | 0 | 440 | 42e8d0c896c201d4feacee1f8cdd0e47739c33c2eb1c968cf05cb68e664baaa3 |
| **Total** | | **1,102 / 1,102** | **264** | **828** | Per-source hashes above |

All eight jobs finished successfully. They reported **zero unparsed
MonoBehaviours**, **zero numeric field/depth truncations**, and no missing
MonoBehaviour path IDs at the declared limits. Their successful status
does **not** establish recovery of original client executable methods,
server-authoritative rules, materials, mesh contents, visual quality or
rights to use original game assets.

## What was found, and what is not yet known

- Weapon **sharedsources** and **modules** include 199 MonoBehaviours,
  animation/renderer and equipment attachment hierarchy references.
  Keyword matches reflect presentation timing, not confirmed ballistics.
- LMG and LBR44 together include 99 MonoBehaviours with 264
  *combat-keyword* field path matches. Inspecting the numeric-only LBR44
  artifact confirms examples such as
  \`<RecoilAnimationData>k__BackingField.<Amplitude>k__BackingField\`,
  \`<RecoilAnimationData>k__BackingField.<Force>k__BackingField\`
  and weapon-inertia weights/lerp speed. These are **animation/handling
  presentation candidates**, not authoritative recoil trajectories,
  damage, hit registration, fire rates or networking rules. They must be
  source-classified before any config is implemented.
- The three Longhorn vehicle variants contain **556 MonoBehaviours**,
  geometry hierarchies, mesh/collider object metadata and 208
  timing/world-keyword field matches. No verified car torque, damage,
  fuel, cargo capacity or server vehicle model was recovered.
- The prison standalone source has **248 MonoBehaviours**,
  **3,622 GameObjects**, **2,039 MeshRenderers**, **277 BoxColliders**,
  **257 MeshColliders** and NavMeshSettings/Occlusion structures.
  Its 440 timing/world matches include blink delay and idle-animation
  pause/range values, **not original arrest, sentence duration, jail,
  escape, police dispatch or recovery formulas**. Two "progression"
  keyword matches correspond to \`BetterMotionBlur.qualityLevel\`,
  a clear false positive caused by substring classification.

**Heuristic keyword totals are not authoritative features.** In particular,
zero economy-keyword matches across these eight bundles is not evidence
that the game has no economy, and "complete_numeric_extraction" only
refers to reachable MonoBehaviour numeric fields under specified limits.

## Coverage and next research

- Documented original source scans: **25 of 330 tracked bundles**.
- Total parsed MonoBehaviours in the source ledger: **10,583**.
- Remaining tracked sources without a documented scan: **305**.
- Historical old numeric overflow records still incomplete: **26**.
- The matching IL2CPP GameAssembly.dll, original server configuration,
  and authoritative economy, weapon, vehicles and police formulas remain
  **unavailable/unverified**.
- No source coefficients were injected into independently authored
  gameplay models. This work is W1 evidence recovery, not W2 design
  approval, a new gameplay feature, or a Unity Editor runtime pass.

Exact source SHA, byte size, Unity object type counts, lexical candidate
counts, and explicit numeric limits are in
\`reconstruction/data/extraction_coverage.json\`. Eight corresponding
\`evidence-*.bundle\` GitHub Actions artifacts retain short-lived numeric-only
path ID and value evidence; raw meshes, sounds, textures and executables
were not exported into the reconstructed game.

Next focused recovery should prioritize unscanned gameplay-rich source
schemas and a type/MonoScript crosswalk, then detailed system contracts
for genuinely absent mechanics. Re-run the same bounded, source-identified
method rather than guess original damage, money, or prison values.
Actual Unity Editor/Play Mode and Windows EXE verification remains
**not run**, under control issue #9.

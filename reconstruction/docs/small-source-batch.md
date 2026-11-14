# W1-F — verified small non-LFS UnityFS batch inventory

**Measured source run:** https://github.com/Nippytime/rabron/actions/runs/43590995615

The Git-tree-backed planner identified exactly **117** previously unscanned
original UnityFS bundles between **1,024 and 999,999 Git blob bytes**, from
a frozen **330-path** tracked inventory. Six bounded matrix batches independently
checked out only their own files with LFS disabled; source byte lengths,
Git blob SHA-1 identity, UnityFS magic, and SHA-256 were checked against
the actual binaries. Python/UnityPy 1.25.4 read-only scans enforced
**2,048 fields and depth 32**, with per-object path IDs, object-type totals,
parse errors and numeric truncation explicitly recorded.

| Measured result | Count |
| --- | ---: |
| Original sources newly inventoried | 117 |
| New source bytes | 27,428,684 |
| New MonoBehaviours parsed / total | 4,272 / 4,272 |
| Bundles with zero MonoBehaviours | 73 |
| Unparsed MonoBehaviours | 0 |
| New field-capped records (localization) | 7 |
| Keyword matches: economy / combat / progression / timing-world | 23 / 1 / 121 / 1,358 |
| All documented source scans | 142 / 330 |
| Total parsed MonoBehaviours | 14,855 |
| Unscanned original bundles | 188 |
| Unresolved old + new field-capped records | 26 + 7 = 33 |

The seven newly capped records occur in the shared localization bundle and
six language table bundles (English, French, German, Portuguese, Russian
and Spanish). These are explicitly partial numeric scans, **not** complete
game data. Zero-MonoBehaviour sources were still validly inventoried as
other Unity object types; they cannot establish game mechanics.

Keyword matches are heuristic paths, not gameplay formulas. The 23
economy-keyword matches occur in the main-menu source. The original
payout, money conversion, recoil, vehicle handling, sentence, server
authority and multiplayer rules remain unverified. No copyrighted
textures, meshes, sound or original scripts were exported.

Every source's SHA-256, Git blob ID, size, parsed count, type counts,
per-category keyword counts and bounded-scan status were recorded in
`reconstruction/data/extraction_coverage.json`; per-object path IDs and
samples are retained as short-lived GitHub Actions artifacts. The
ledger records measured source evidence only. A later PR run rechecks
documented W1-F source bytes and requires all fields to match rather than
producing a misleading empty extraction matrix.

Next W1 tasks: bounded scans of 156 uninspected medium, 12 large and
20 LFS-pointer sources, plus review of the 33 partial numeric records and
missing matching IL2CPP method/server authority. Unity Editor, Play Mode
and Windows EXE acceptance under #9 have not been executed.

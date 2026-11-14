# ROB RUN — verified Git LFS bundle inspection

Source run (both matrix jobs succeeded after fixing the file-exclusion bug):
https://github.com/Nippytime/rabron/actions/runs/43534837573

Run-specific evidence:
- shared-global: artifact \`lfs-source-evidence-shared-global\`, artifact ID 14089237099.
- settlement: artifact \`lfs-source-evidence-settlement\`, artifact ID 14089342092.
- Tool: UnityPy 1.25.4 with read-only parsing and field path/category audit.

## Genuine UnityFS objects downloaded

| Bundle | Original SHA-256 | Bytes | Parsed MonoBehaviours | Numeric-field limits | Notes |
| --- | --- | ---: | ---: | ---: | --- |
| shared-global_assets_all.bundle | 2852ce0712e962a4d8995ebd4e80c2cd03381c56ac0b6c08a5587e3b869c77a9 | 57,128,016 | 5/5 | 0 | Contains animation clips, meshes, 373 sprites, and a few camera/light effects |
| location-settlement-data_assets_all.bundle | 43018ce5ec95c4dfdd433b71d1460ada17cf4dbd79d8abbd70c2bf00b5c83534 | 128,804,483 | 3,220/3,220 | 12 | Contains scene prefabs, collisions, and some player-facing configuration |

**Both bundles were verified against the SHA-256 embedded in their Git LFS
pointer**, so the tool processed real original bytes rather than 133-byte
pointer text. No MonoBehaviour parse exceptions were reported. The settlement
extraction is still partial because 12 records exceeded the field cap.

The shared-global heuristic emitted one apparent combat field
\`FlareData_Indoor_Lamp_01.elements[0].lengthSpread\`. This is a **lens flare
presentation setting, not a ballistic spread formula**. Do not count it as
evidence of combat tuning. The other priority effect assets include camera
shake and handheld camera behavior.

## Concrete settlement finding: visible cash pile intervals

The settlement bundle contains **three unnamed serialized MonoBehaviours**
with the field \`<MoneyWorkbenchCashPileSizeIntervals>k__BackingField\`.
These are exact serialized integer sequences:

| Unity path ID | Threshold count | Largest observed threshold |
| --- | ---: | ---: |
| -3521504050020868324 | 16 | 50,000,000 |
| 1509660387188884686 | 11 | 1,000,000 |
| 5308116492309360796 | 14 | 15,000,000 |

Common first 11 thresholds:

\`0, 1, 1000, 5000, 10000, 25000, 50000, 100000, 250000, 500000, 1000000\`

The 14-threshold object appends \`2000000, 5000000, 15000000\`.
The 16-threshold object additionally appends \`30000000, 50000000\`.

A source-anchored, machine-readable record is preserved as
\`reconstruction/data/settlement_cash_pile_thresholds.json\`.
The thresholds plausibly control how the physical cash pile's visual size
responds to stored amounts; the selection algorithm, object/variant mapping,
underlying currency units and any money laundering rate are **not** recovered.
They must not be equated to payout caps, laundering conversion or server-side
currency balancing.

## Implications for next phase

- Recovering Unity asset data is technically possible, including Git LFS
  content when selectively fetched.
- The client data provides asset/scene layout, visual feedback, and some user
  interface parameters. It has **not** yet revealed a reliable economy and
  combat balance schema.
- Matching IL2CPP \`GameAssembly.dll\` was not included in the original upload.
  Server-side calculations and persistence may be unavailable from client
  binaries even with matching code.
- Next reconstruction work should prioritize a playable, independently
  authored core loop with configurable parameters, clearly marking
  **verified behavior** versus **provisional balancing**. Run measured
  gameplay comparisons before making parity claims.

No proprietary meshes, textures, or sounds are redistributed by the authored
reconstruction files. The reference game bundles remain untouched.

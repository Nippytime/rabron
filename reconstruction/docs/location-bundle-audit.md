# ROB RUN location-bundle extraction — first verified pass

## Provenance

GitHub Actions successful run: https://github.com/Nippytime/rabron/actions/runs/43534168289

Scanner: reconstruction/tools/extract_unity_bundle.py (UnityPy 1.25.4)
Categorizer: reconstruction/tools/summarize_numeric_evidence.py

This is a **read-only inspection of shipped client assets**, not recovered game
source, not a measured server balance table, and not a playable reimplementation.
All paths below are under StreamingAssets/aa/StandaloneWindows64/.

### Actual UnityFS bundle results

| Bundle name (suffix \`_assets_all.bundle\`) | MonoBehaviours parsed / total | Numeric field records truncated at 256 | Economy candidate fields | Combat candidate fields | SHA-256 of input bundle |
| --- | ---: | ---: | ---: | ---: | --- |
| location-city-data | 31/31 | 2 | 0 | 0 | 2ca8ae45348fff1c9c3359a0e82afa39f7fe9df41fcadbbffab9df1b11b73e56 |
| location-hub-data | 248/248 | 5 | 0 | 0 | 6fd2d0d3c6f65724cb77b10191b053a795ded2bab0259e7b6f94cee815bef537 |
| location-prison-data | 181/181 | 0 | 0 | 0 | c7f6971cbfce40b9942de8774226a2ba9d717269dbc130df5a17d3b566b42e09 |
| location-sectorcenter-data | 26/26 | 1 | 0 | 0 | 864c3b64feeebd62784515af9595a5fe1169213acaddbddfb39823e66529928a |
| location-settlement2-data | 1/1 | 1 | 0 | 0 | 2a951aa3587d0999334dd6ea878ed47cc65f480ea4320c41776b473c23df13c2 |
| inbuild | 150/150 | 10 | 0 | 0 | d4bff10e5f31e8e10b3bbf979aa6ee872bed5daff59765b1837fe1d733747531 |
| **Total** | **637/637** | **19** | **0** | **0** | Per-bundle checksums above |

Each run generated a raw.json file and a small summary.json file in its
short-lived per-bundle \`source-evidence-*\` GitHub Actions artifact.

**Interpretation:** The zero values mean the keyword-filtered summary did not
identify those categories, not that the game has no economic/ballistic formulas.
The scanner examines selected serialized MonoBehaviours, not every serialized
Unity object or game-server configuration. Unnamed objects, omitted fields,
and binary code remain major coverage gaps. A green workflow does not imply
the game formula is known.

## Confirmed Git LFS gaps

The GitHub tree contains *pointer text*, not UnityFS bytes, at these paths:

| Bundle | Git LFS OID (SHA-256) | Real object size as declared by pointer |
| --- | --- | ---: |
| location-settlement-data_assets_all.bundle | 43018ce5ec95c4dfdd433b71d1460ada17cf4dbd79d8abbd70c2bf00b5c83534 | 128,804,483 bytes |
| shared-global_assets_all.bundle | 2852ce0712e962a4d8995ebd4e80c2cd03381c56ac0b6c08a5587e3b869c77a9 | 57,128,016 bytes |
| npc_assets_all.bundle | aacec65903186775c8b834ba89cbbc0fea1419d857f14a0d95943732f12a0d69 | 98,896,651 bytes |
| tutorial_assets_all.bundle | 56f1993ad49ac265c3268667557b0ec13c1c0f39fb7ada94ae4251e4328ac691 | 84,166,120 bytes |

The scanner now fails with an explicit Git LFS-pointer message before attempting
to parse such files. If Git LFS downloads are available, these original bytes
should be analyzed next, especially shared-global and settlement data.

## Prior source bundle findings

The 38 MB scriptableobjects_assets_all.bundle was inspected separately:
3,925/3,925 MonoBehaviours parsed, with 25 field-output truncations at a
4,096-field limit. Representative values include client-side weapon crosshair
spread offsets and camera recoil amplitudes. The GrandHeistViewDescriptions,
MoneyWorkbenchViewDescriptions and CargoSellViewDescription assets inspected
so far predominantly store localization references and presentation settings.
See scriptableobjects-first-pass.md and scriptableobjects-full-pass.md for
measured results. These are not game economy formulas.

## Next milestone for playable parity

1. Obtain the original Git LFS asset contents legitimately; parse their data
   and classify each field as visual presentation, client gameplay config,
   server-authoritative rule or unknown (never infer last category from a name).
2. Extract authoritative economic and combat values from matching runtime data
   if present, otherwise collect reproducible black-box game observations.
3. Implement a clean-room playable Unity prototype based on a behavior contract
   that distinguishes recovered numbers from proposed tuning.
4. Verify the full core loop and update rule tables against repeatable
   gameplay sessions. No exact parity claims until behavioral comparisons pass.

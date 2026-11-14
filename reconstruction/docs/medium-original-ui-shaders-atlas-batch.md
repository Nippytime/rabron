# W1-Y: original shader, tattoo scene, achievement and UI sprite-atlas source evidence

**Actual original-byte source run:** https://github.com/Nippytime/rabron/actions/runs/43646079579

Ten original Git-tracked UnityFS bundles were read-only scanned with pinned UnityPy
**1.25.4** in five sparse-checkout batches of two source files, with at most two
batches concurrently and hard timeouts. The exact Git SHA-1/byte-length source
pins in `reconstruction/data/medium_original_ui_shaders_atlas_source_targets.json`,
UnityFS signatures and independently computed source SHA-256 were checked against
the original binaries. Numeric scans were bounded to **2,048 fields/depth32**.
No copyrighted shader, sprite, texture, model or audio payload was exported.

| Original source | Verified bytes | MonoBehaviours parsed/total | Original source SHA-256 |
| --- | ---: | ---: | --- |
| `shaders_assets_all.bundle` | 14,633,538 | 0/0 | `9f10f7434ad49ca275d511c3c8847d76e848e5c739855a9ec07b6fb37e4176ac` |
| `tattoo_scenes_tattoounlock.bundle` | 2,726,770 | 94/94 | `a37e7b6246882363fa549a59264db5576a0af7233c153aeea13359c904fbc4f1` |
| `ui-spriteatlas-4k_assets_assets_content_ui_sprites_4k_achievementboard_achievementboard_4k.spriteatlasv2.bundle` | 2,572,274 | 0/0 | `25eee2886f8e22298fffa9588f16abbf6a8ea348837fa929421ad20953f53039` |
| `ui-spriteatlas-4k_assets_assets_content_ui_sprites_4k_achievementboard_achievementboard_qhd.spriteatlasv2.bundle` | 2,376,885 | 0/0 | `efb1e38fc1963f6f7a837b482a99d0377db3b18016f9e2d3dba1762e717cb5cd` |
| `ui-spriteatlas-4k_assets_assets_content_ui_sprites_4k_all__fullspriteatlas_hd.spriteatlasv2.bundle` | 9,252,721 | 0/0 | `ba1929524e0cc9268bd84e79eb77254cea10fa2ef81c6b8a4ab66d2a24bb1407` |
| `ui-spriteatlas-4k_assets_assets_content_ui_sprites_4k_all__fullspriteatlas_qhd.spriteatlasv2.bundle` | 15,949,340 | 0/0 | `53befb5f121954ed8b34b47446c3b7bfdc6155d3b02948fdc9eed34ceec6d473` |
| `ui-spriteatlas_assets_carsspriteatlas_4k.bundle` | 1,405,211 | 0/0 | `a3e307119b5aaf5cc1043af7a5715430308c4a3acb1a6b1adbff71025908fe35` |
| `ui-spriteatlas_assets_weaponsspriteatlas_4k.bundle` | 2,251,297 | 0/0 | `e0793fddd011f1758e0558092dee9291574d771ed2e4eb20635d858aa401f357` |
| `ui-spriteatlas_assets_weaponsspriteatlas_hd.bundle` | 2,209,627 | 0/0 | `9c769f0ddf6fb20e46382b1855fa09a766c570a15d6cb6df46a50702925ee854` |
| `ui-spriteatlas_assets_weaponsspriteatlas_qhd.bundle` | 2,209,641 | 0/0 | `a76ea5a4d95ef8313af90fc179d1a1dd0254d009a9a94f7ea4ad71abc24a5b83` |
| **Total** | **55,587,304** | **94/94** | Ten source-verified digests |

Measured original Unity object-type totals: **155 Shader**, **6 ComputeShader**,
**6 ShaderVariantCollection**, **54 Material**, **33 Texture2D**, **137 Sprite**,
**8 SpriteAtlas**, **439 GameObject**, **437 Transform**, **86 MeshRenderer**,
**32 SkinnedMeshRenderer**, and **4 Mesh**. The tattoo-unlock scene contained
**94/94** parsed MonoBehaviours, while the other nine bundles had genuine
**zero MonoBehaviours** despite their documented Unity object inventories.

Across the ten original sources: **zero unparsed records**, **zero new field
caps**, and **105 keyword candidate numeric fields** (2 progression, 103
timing/world, none combat/economy). These are client serialized-field candidates,
not source-authoritative gameplay formulas or complete raw media extraction.
Every recorded scan retains `documented_scan_not_fully_verified` source-scope
status; bounded MonoBehaviour parsing cannot validate IL2CPP/server systems.

The measured evidence ledger documents **288/330** original UnityFS sources
and **82,125** parsed MonoBehaviours. **42** original bundles remain unscanned
(22 medium non-LFS, 20 LFS), with **42 older unresolved numeric caps**.

**Merge gate:** after committing the measured data, require another nonempty
**all-ten-original latest-head source-byte recheck** plus all historical
source/numeric/LFS/Python workflows successful. Missing, skipped, queued,
running, failed and zero checks never pass. Do not merge without unchanged
head/base verification and post-merge `dev` Python CI.

**Unverified:** original IL2CPP/GameAssembly.dll methods and server authority,
proprietary media reuse rights, Unity 6000.3 Editor/Play Mode and Windows EXE
acceptance (issue #9), and the W2–W8 full-game implementation.

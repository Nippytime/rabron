# ScriptableObject evidence — first binary pass

Provenance:
- Scanner: reconstruction/tools/extract_unity_bundle.py, UnityPy 1.25.4.
- GitHub Actions run: https://github.com/Nippytime/rabron/actions/runs/43532996042
- Run artifact: scriptableobjects-index (artifact ID 14087384894).
- Source bundle SHA-256: 239f015bc6f351dc315ac403a2758efacfb167cab05188e05082e76ee021b4fd.
- Source path: StreamingAssets/aa/StandaloneWindows64/scriptableobjects_assets_all.bundle.

## Extraction results

- Bundle size: 38,546,478 bytes.
- Unity object types include 3,925 MonoBehaviour entries, 41 Mesh, 28 Material, 24 Texture2D, 2 AnimationClip, and several other Unity component types.
- The discovery pass attempted **2,000/3,925** MonoBehaviour records and **parsed all 2,000**. No parse exceptions were reported.
- **1,925 objects were not attempted**, due to the intentional first-pass cap.
- 28/2,000 parsed records also hit the 512-numeric-field cap. Thus the initial scan is **partial** despite passing CI.
- The follow-up workflow will attempt every MonoBehaviour with a larger field cap. An asset parse does **not** establish the authoritative network-side gameplay formula.

## Recoverable numeric presentation settings

The following are actual values read from the bundle, not approximations.
They describe **client-facing ViewDescription fields**, so they must not be
misrepresented as underlying weapon damage, ballistics, or hit probability.

| Asset name | Unity path ID | MinAimSpreadCrossPointerOffset | MaxAimSpreadCrossPointerOffset | MinHipSpreadCrossPointerOffset | MaxHipSpreadCrossPointerOffset |
| --- | --- | ---: | ---: | ---: | ---: |
| pdw_90_m_1_WeaponSpreadViewDescription | -8646834918548576430 | 0.75 | 2.0 | 2.0 | 3.0 |
| kl_545_m_2_WeaponSpreadViewDescription | -7049371399790212618 | 0.5 | 1.5 | 1.5 | 2.5 |
| rc_556_m_3_WeaponSpreadViewDescription | -6855668014232651526 | 0.5 | 1.5 | 1.5 | 2.5 |

Additional verified sample: dp_9_m_1_WeaponShotCameraViewDescription
(path ID -9083254849099821901) contains CameraFovKickAmplitude = 0.25,
CameraFovKickAttackTime approximately 0.05, and CameraRollKickAmplitude
approximately 0.30. These are camera presentation parameters, not weapon damage.

## Next interpretation steps

1. Finish all 3,925 MonoBehaviour records and record any failed or truncated fields.
2. Group objects by script/class and extract economically relevant fields from
   authoritative-looking configuration assets rather than animation curves,
   player display formatting, or localization pointers.
3. Cross-reference any recovered value against runtime observations and
   server-authoritative behavior before putting it in the playable simulation.
4. Continue inventorying other bundles as needed, without copying proprietary
   graphics/sounds into a redistributed independent game.

The current evidence is sufficient to reconstruct selected weapon UI behavior,
not to claim that ROB RUN's complete gameplay formulas have been recovered.

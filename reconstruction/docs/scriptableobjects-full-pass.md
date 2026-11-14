# ScriptableObject evidence — complete object pass, partial field extraction

Source: StreamingAssets/aa/StandaloneWindows64/scriptableobjects_assets_all.bundle
Source SHA-256: 239f015bc6f351dc315ac403a2758efacfb167cab05188e05082e76ee021b4fd
UnityPy version: 1.25.4

Observed run: https://github.com/Nippytime/rabron/actions/runs/43533207312
Artifact: scriptableobjects-index, GitHub Actions artifact ID 14088805964.
CI scanner revision: f0d76e0113eda5785b3970fc2e09ae412d000a38.

## Measured coverage

| Metric | Result |
| --- | ---: |
| Unity MonoBehaviour objects in bundle | 3,925 |
| MonoBehaviours attempted | 3,925 |
| Parsed successfully | 3,925 |
| Parse exceptions | 0 |
| Objects truncated at 4,096 numeric fields | 25 |
| No. of non-MonoBehaviour object types | 10 |
| Is numeric extraction complete? | **No** |

The 25 truncated objects are primarily large localized dialogue/animation or
view-description assets (e.g., player dialogue text configuration, inventory UI,
vehicle display config, weapon view config). All 3,925 object headers and
typetrees could be decoded, but the scanner intentionally caps individual
numeric outputs. The completeness flag must remain false.

The bundle is rich in **client rendering and presentation data**; class names
such as ViewDescription and ViewConfiguration are not evidence that numeric
economic rates are authoritative or even present. Some fields are pointers
(m_FileID/m_PathID), localization keys or animation values rather than game
balance parameters.

## Concrete field-level samples

These are unmodified serialized values tied to name and path ID. They are
suitable as reference evidence for reproducing UI feedback, not proven physics.

| Serialized asset | Unity path ID | Example serialized value |
| --- | --- | --- |
| pdw_90_m_1_WeaponSpreadViewDescription | -8646834918548576430 | MinAimSpreadCrossPointerOffset = 0.75; MaxAimSpreadCrossPointerOffset = 2.0 |
| kl_545_m_2_WeaponSpreadViewDescription | -7049371399790212618 | MinAimSpreadCrossPointerOffset = 0.5; MaxAimSpreadCrossPointerOffset = 1.5 |
| rc_556_m_3_WeaponSpreadViewDescription | -6855668014232651526 | MinHipSpreadCrossPointerOffset = 1.5; MaxHipSpreadCrossPointerOffset = 2.5 |
| dp_9_m_1_WeaponShotCameraViewDescription | -9083254849099821901 | CameraFovKickAmplitude = 0.25; CameraRollKickAmplitude = 0.30 |

The values are from the saved bundle artifact. Unity floating-point storage
can produce minor round-off differences; human-readable values are rounded.

## Next analytical work

1. Inspect the still-truncated 25 objects selectively, raising field limits
   only where their schema is relevant to an observable mechanic.
2. Extract **named gameplay state** from location data bundles, shared-global,
   and potential server-delivered settings. Compare with the visual-only
   ScriptableObject references in this bundle.
3. Map Unity path IDs to MonoScript class identity and materialize only
   explicitly supported numeric rules.
4. Confirm each gameplay coefficient against a matching client/server build.
5. Keep a provenance ledger: (source bundle SHA-256, Unity path ID, field name,
   value, classification: UI presentation / game config / unresolved).

Do not label any of these numbers as an exact damage, heist payout, tax or
money-laundering formula until corroborated. This is a measured **asset
extraction**, not a full game recreation.

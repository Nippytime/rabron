# ROB RUN-style prototype — Unity 6.3

**Status: source implementation; Unity Editor / packaged build not yet smoke-tested.**

This is an independently authored playable **prototype design**, using Unity
primitives and the tested reconstruction gameplay core. It is not the original
ROB RUN source or a claim of numerical/mechanical parity.

## Small clone (recommended on Windows)

The source repository holds a large reference-game binary inventory; the
prototype only needs the \`reconstruction/\` subtree. From PowerShell:

~~~powershell
git clone --filter=blob:none --sparse https://github.com/Nippytime/rabron.git
cd rabron
git sparse-checkout set reconstruction
~~~

This avoids downloading the original Unity assets to open the prototype.
The local gameplay package still resolves because it also lives inside
\`reconstruction/\`.

## Open and play

1. Install Unity **6000.3.18f1** (or compatible Unity 6000.3 release) with
   Windows build support if you intend to produce a Windows executable.
2. Open **this folder** in Unity Hub:
   \`reconstruction/unity-prototype/\`
   (do not open the repository root).
3. Wait for Package Manager import. The manifest pins
   \`com.unity.inputsystem@1.20.1\` and references the gameplay core as a
   **local package** at \`../../game/Core\`. The original game content folder
   is never imported into the Unity project.
4. If Unity asks to enable its new Input System, click **Yes** and allow the
   requested Editor restart. Only the Input System backend is supported.
5. On first launch, the Editor helper creates \`Assets/Scenes/Prototype.unity\`
   and adds it to Build Settings. If it is not open automatically, run
   **Tools > Rabron > Prepare Demo Scene** and open the scene.
6. Press **Play**. The procedural world, camera, player, markers and UI
   instantiate when the scene loads. No external assets are required.
7. To build an executable after local Editor validation, select
   **Tools > Rabron > Build Windows Prototype**. Unity writes
   `Builds/RabronPrototype.exe` and its data folder. Windows Build Support
   must be installed through Unity Hub; this repository does not contain
   a prebuilt EXE.

## Verifiable Unity Editor smoke test (Windows)

The source-only CI cannot prove that Unity compiles or plays the project.
A real Unity 6000.3.18f1 installation can run the authored Editor smoke
test and optionally build a Windows executable in a deterministic CLI session.

Close the project in the graphical Unity Editor first, then run from
the repository root in PowerShell:

~~~powershell
# Compiles the project in Unity and checks procedural station/collider setup
.\reconstruction\unity-prototype\Tools\Verify-Unity.ps1

# Also builds and verifies a Windows executable and its data directory
.\reconstruction\unity-prototype\Tools\Verify-Unity.ps1 -BuildWindows

# With a custom Unity installation path
.\reconstruction\unity-prototype\Tools\Verify-Unity.ps1 -EditorPath 'D:\Unity\6000.3.18f1\Editor\Unity.exe' -BuildWindows
~~~

The runner locates Unity through the normal Unity Hub installation path
(or uses the UNITY_EDITOR environment variable or -EditorPath), starts
Unity in -batchmode, and inspects Logs/editor-smoke.log. It requires both
a zero Unity exit code and an explicit smoke success token. Builds also
require the EXE and matching data directory. It fails instead of reporting
a false green when Unity is missing, package import fails, or checks fail.

The Editor smoke checks generated procedural geometry, all 14 station
types and trigger colliders, the 0.65m step offset needed to climb the
fence platform, and the heist-to-bank behavior contract. The optional
build requires Windows Build Support and produces
Builds/RabronPrototype.exe inside the Unity project.

Launching the EXE remains necessary to verify input, camera, HUD, and
the full interactive play-mode loop. The first Editor import might
need a graphical session to activate the Input System.

**Verification status:** The hosted GitHub CI has not executed
Unity Editor or built a Windows player. Passing Python, .NET, and
PowerShell syntax checks cannot establish Unity runtime success.

## Controls

| Action | Keyboard / mouse | Gamepad |
| --- | --- | --- |
| Move | WASD | Left stick |
| Look | Mouse | Right stick |
| Sprint | Left Shift | Left-stick click |
| Interact at a highlighted pillar | E | South face button (A) |
| Release mouse cursor | Escape | — |
| Lock cursor again | Left click in the Game view | — |

## Complete sample loop

The top-left HUD shows your heist phase, player role, money accounts, alarm
state, objective and controls. Available interaction pillars illuminate
around the city.

1. Walk **north** to the cyan *Scout* pillar outside the warehouse.
2. Put on the **red mask** at the neighboring pillar.
3. Use the amber entrance pillar to **begin the heist**.
4. Walk through the 4 m opening and collect one or both loot objects.
5. Leave the building; use the **Escape** pillar on the road.
6. Go **west** to the fence counter. Selling now reveals four original
   green cash-bundle meshes **on top of the counter**; they are visual only,
   with no collision. None of the cash is added to your wallet yet.
7. Walk around the counter to its collection marker and press **E / A**.
   The bundle meshes disappear and the balance moves from Counter Cash to
   Dirty Cash. The next destination is the **eastern** laundry workstation.
8. Laundering finishes after an adjustable demo timer. Go **south** to the
   city-exit marker to clear criminal status and use the return marker.
9. As a **civilian**, open the bank account at the ATM if not already open,
   and deposit clean cash. A nearby new-heist station resets just the
   heist phase and retains account balances.

The prototype currently has no NPCs; alarm escalation is not simulated.

The physical cash bundle display is a **generic presentation placeholder**,
not a reproduction of ROB RUN cash denomination meshes or the extracted
money-workbench pile thresholds. Those reference thresholds are recorded
separately and are not assumed to control fence payouts or visual sizes.

## Adjust demo values without modifying code

These values are **provisional test figures**, not recovered ROB RUN balance:

- Artwork quote: 120 demo units
- Watch quote: 80 demo units
- Clean payout: 80% of submitted dirty cash
- Laundering time: 8 seconds

To override them, in Unity use **Assets > Create > Rabron > Prototype Economy**,
configure the ScriptableObject in the Inspector, and save it as
\`Assets/Resources/DemoEconomy.asset\`. The runtime loads it automatically.
No hard-coded economic rates live in the portable \`HeistSession\` core.

## Implementation

- \`Assets/Scripts/PrototypeBoot.cs\`: on-scene-load composition root.
- \`Assets/Editor/PrototypeSceneInstaller.cs\`: create default empty scene and
  build settings, one time when the Editor opens the project.
- \`PrototypeWorld.cs\`: asset-free scene blockout and interaction targets.
- \`ThirdPersonMotor.cs\`: input, collision, movement and follow camera.
- \`PrototypeDirector.cs\`: calls portable game core APIs on interaction.
- \`PrototypeHud.cs\`: runtime UI Toolkit status, objective and prompts.
- \`PrototypeBalance.cs\`: explicitly non-source demo quotes and timing.
- \`../../game/Core/HeistSession.cs\`: **single** gameplay state implementation
  shared with the .NET test harness via a local UPM package.

## Validation and limitations

GitHub Actions checks the referenced local package, all 14 interaction targets,
Unity project manifest, demo bootstrapping and code separation. The original
.NET console tests compile and exercise money conservation and phase gating.
**Neither test substitutes for opening the actual project in Unity Editor.**

Still missing: a real Unity Editor scene/build smoke test; exported Windows EXE;
police AI, dynamic alarms, human multiplayer, base building, vehicles, cargo,
clans, prison, persistent server state, realistic art or animations; measured
matching heist payouts, loot tables, laundering ratios and timers. The logic
uses provisional restrictions and is **not claimed to match ROB RUN exactly**.

The shipped original Unity player files are only evidence, not redistributed
game assets. Do not publish the original game resources without rights.

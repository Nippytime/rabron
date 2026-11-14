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
   \`com.unity.inputsystem@1.20.1\` and enables Unity's built-in Physics, Audio and UI Toolkit
   modules. It references the gameplay core as a
   **local package** at \`../../game/Core\`. This local package path is relative to the project's Packages
   directory, not the shell's working directory. The original game content
   folder is never imported into the Unity project.
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
Unity in -batchmode, and inspects Logs/editor-smoke.log. The Editor
creates the scene through AssetDatabase and writes Windows build outputs
inside the Unity project irrespective of the shell's current directory.
The smoke check fails if the new Input System backend is disabled; enable
it in Player Settings and restart Unity. The runner requires both
a zero Unity exit code and an explicit smoke success token. Builds also
require the EXE and matching data directory. It fails instead of reporting
a false green when Unity is missing, package import fails, or checks fail.

The Editor smoke checks generated procedural geometry, all 15 station
types and trigger colliders, solid-wall interaction occlusion, near-wall
camera placement, the 0.65m step offset needed to climb the fence platform,
and the heist-to-bank behavior contract. The optional
build requires Windows Build Support and produces
Builds/RabronPrototype.exe inside the Unity project.

Launching the EXE remains necessary to verify input, camera, HUD, and
the full interactive play-mode loop. The first Editor import might
need a graphical session to activate the Input System.

**Verification status:** The hosted GitHub CI has not executed
Unity Editor or built a Windows player. Passing Python, .NET, and
PowerShell syntax checks cannot establish Unity runtime success.

## Real Unity Play Mode acceptance (Windows)

The prototype now includes two Unity Test Framework Play Mode acceptance
tests. These run **inside Unity** and are not simulated by the Python/.NET
CI pipelines:

- Runtime bootstrap: live director, player controller, camera, UI Toolkit
  HUD, guard, cash presenter and 15 station markers
- Full gameplay dispatcher: scout, mask, robbery, guard control, loot,
  escape, sell, physical counter pickup, laundering, city exit and return,
  bank deposit and next-heist reset

The heist test calls the production dispatcher directly via reflection,
not synthetic keyboard input. Manual WASD/gamepad controls, live physics
reachability, visual presentation and the packaged Windows EXE still
require a human playthrough.

Close the graphical Unity Editor first, then run from repository root:

~~~powershell
.\reconstruction\unity-prototype\Tools\Verify-PlayMode.ps1

# With a custom Editor location
.\reconstruction\unity-prototype\Tools\Verify-PlayMode.ps1 -EditorPath 'D:\Unity\6000.3.18f1\Editor\Unity.exe'
~~~

Unity test discovery uses a **dedicated Editor-only test assembly** with
NUnit, UnityEngine.TestRunner and UnityEditor.TestRunner references, as
required by Unity's assembly definition documentation. The tests are not
included in ordinary packaged Windows builds.

The NUnit result acceptance gate is independently exercised in GitHub
Actions with synthetic successful, missing, malformed, failed and duplicate
test reports, so CI can validate the gate without pretending to run Unity.
Those fixture tests provide **no evidence of a real Unity Play Mode run**.

The runner uses Unity's -runTests -testPlatform PlayMode commands WITHOUT
-quit, which Unity does not support during tests. The selected test category
is RabronPlayMode. It writes Logs/playmode-results.xml (NUnit) and
Logs/playmode-tests.log. It removes stale results and requires a successful
process exit, passing NUnit result, at least two passed cases, zero failed
cases, and both named acceptance methods. Zero-test runs fail.

During batchmode Unity test runs, demo checkpoints use an isolated
Application.temporaryCachePath/rabron-playmode-tests/ directory rather
than the developer's real save. Source-level CI only syntax-lints the
PowerShell runner and checks structural test coverage; it **does not**
execute Unity. A real NUnit report is needed before reporting an actual
Play Mode pass.

Unity reference:
https://docs.unity.com/en-us/engine/6000.3/manual/programming-environment/test-framework-introduction/running-tests/run-tests-from-command-line

## Local progress saving

The local **demo** now retains the authoritative gameplay session between
Play Mode sessions and Windows executable launches. On startup it loads a
versioned checkpoint from Unity's \`Application.persistentDataPath\`.
Successful interactions, guard alarms, completed laundering, application
pause and quit trigger saves. You can stop during a heist, with uncollected
fence money, or while a laundering timer is running, then resume without
minting extra currency. A timer that expired while the app was closed
completes on the next gameplay update.

The file is \`rabron-prototype-v1.json\` with a \`.bak\` previous checkpoint.
The app saves via a temporary file and replacement, preserving the earlier
version on each completed write. It validates restored roles, stages, loot,
balances, and any pending laundering payout/deadline; corrupt or unsupported
checkpoints are rejected, with a previous valid backup used if available.
No game binaries or personal account credentials are stored.

To start a clean demo, **close Play Mode/the game**, then remove both
\`rabron-prototype-v1.json\` and \`rabron-prototype-v1.json.bak\`
inside Unity's persistent data directory. This is a **local-only prototype
checkpoint**, not the original game's server save, multiplayer account,
seven-day wipe, or protected bank ledger. Only gameplay state is saved;
the character respawns at the city start (or the desert return marker
when outside the city), not at the previous exact coordinate.

The Unity Editor smoke test additionally exercises real \`JsonUtility\`
roundtrips for collectible counter cash and an in-progress laundering
job. As with every Editor test, it **must actually run inside Unity** before
its result can be claimed as verified.

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
4. Walk through the 4 m opening. A stationary red guard faces the warehouse
   entrance. Stay outside his **demo-only** forward vision cone and
   approach the pink **Control guard** pillar from the side to prevent
   future alarms. You can also risk being seen, which raises the alarm.
   Collect one or both loot objects.
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

The prototype has one stationary guard **placeholder** whose line-of-sight
sensor raises the existing heist alarm if the player is seen. Controlling
the guard prevents subsequent detection but cannot erase an existing alarm.
This implements a small prototype of the official "keep staff controlled
to prevent alarms" behavior, not the original NPC AI, detection distance,
police dispatch, arrest or wanted-level rules. Patrol movement and police
response are not implemented.

### Physical access and camera

Nearby pillars now require a clear ray from the player's eye: a solid
warehouse wall or fence counter prevents interaction from its opposite side.
The cash-pickup station is therefore on the **rear** side of the counter;
walk around to it rather than interacting through the front.
Trigger colliders do not obstruct the ray. The third-person follow camera
moves in front of solid walls rather than clipping through them. Both systems
reuse preallocated physics-hit buffers instead of allocating on every frame.

The Editor smoke test probes the generated warehouse wall to verify that
loot cannot be accessed from the street, can be accessed from the inside,
and that the camera is clamped before that wall. These are **source-backed
test cases**, not proof of a tested Unity player until the real Editor
validation is run.

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
- \`GuardSensor.cs\`: stationary guard sight cone with provisional demo tuning.
- \`ThirdPersonMotor.cs\`: input, collision, movement and follow camera.
- \`PrototypeDirector.cs\`: connects interactions and save/load to the gameplay core.
- \`PrototypeSaveStore.cs\`: Unity-only JSON/file adapter for local checkpoints.
- \`PrototypeHud.cs\`: runtime UI Toolkit status, objective and prompts.
- \`PrototypeBalance.cs\`: explicitly non-source demo quotes and timing.
- \`../../game/Core/HeistSession.cs\`: **single** gameplay state implementation
  shared with the .NET test harness via a local UPM package.

## Validation and limitations

GitHub Actions checks the referenced local package, all 15 interaction targets,
versioned save adapters and invariant validation,
Unity project manifest, demo bootstrapping and code separation. The original
.NET console tests compile and exercise money conservation and phase gating.
**Neither test substitutes for opening the actual project in Unity Editor.**

Still missing: a real Unity Editor scene/build smoke test; exported Windows EXE;
police dispatch, mobile guard AI, human multiplayer, base building, vehicles, cargo,
clans, prison, persistent server state, realistic art or animations; measured
matching heist payouts, loot tables, laundering ratios and timers. The logic
uses provisional restrictions and is **not claimed to match ROB RUN exactly**.

The shipped original Unity player files are only evidence, not redistributed
game assets. Do not publish the original game resources without rights.

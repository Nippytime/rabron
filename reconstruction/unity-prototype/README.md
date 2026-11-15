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

## Original gameplay sound feedback

The prototype now generates three short, **original sound cues** in memory
when the procedural scene starts. A rising confirmation tone plays when a
station action succeeds or laundering completes, a lower tone signals
invalid or out-of-range interactions and custody consequences, and a distinct
alarm sweep plays when the warehouse guard triggers security. The tones use
Unity's built-in AudioSource, not copied reference-game music, sound effects,
asset bundles, or external downloads. All PCM clips are synthesized once,
played as non-looping one-shots at a restrained volume, and destroyed with
their runtime presenter. Batch-mode acceptance does not play sound, so it
does not need audio hardware.

Existing Unity Play Mode source checks the three generated clips for nonzero
samples, but **actual audible sound, level, timing and Windows device output
remain unverified**. Verify those during the human Unity/Windows acceptance
required by parent issue #9. There is no soundtrack, voice system or final
audio mix in this early demo.

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

The Editor smoke checks generated procedural geometry, all 21 station
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

## One-command real Unity acceptance evidence (Windows)

Use this after committing a known source revision, with the Unity project
**closed in the graphical Editor**. This command runs the existing Editor
smoke, real Play Mode NUnit and Windows build validation **in sequence**,
and stops if any stage fails. It also runs a bounded **headless smoke of the
actual freshly built Windows player** after the Unity build:

~~~powershell
.\reconstruction\unity-prototype\Tools\Verify-Acceptance.ps1

# Alternate installed Editor (requires real Unity, not a mock):
.\reconstruction\unity-prototype\Tools\Verify-Acceptance.ps1 -EditorPath 'D:\Unity\6000.3.18f1\Editor\Unity.exe'
~~~

The combined gate refuses a missing Editor, non-Windows host, **incorrect
actual Unity Editor version**, dirty tracked reconstruction files, **unexpected
untracked Unity acceptance inputs**
(any authored Assets, Packages, ProjectSettings, Tools or C# files in the linked
`reconstruction/game/Core` package), missing Play Mode results, stale
executable, empty build data, missing/failed/timed-out Windows Player startup,
or a missing fresh runtime pass marker. Normal Unity-generated `.meta`
files **inside Assets only** and the single auto-created
`Assets/Scenes/Prototype.unity` are exceptions. Ignored Unity Library, Temp,
build logs and IDE files remain excluded. Commit or remove unexpected inputs
before producing evidence for a particular tracked Git revision. The generated scene must be
nonempty after the Editor smoke gate and retain the exact same SHA-256 through
Play Mode and the Windows build; a changed scene fails acceptance.

Before the Editor smoke, the preflight invokes the supplied **actual Unity
Editor executable** with its officially documented `-version` flag, requiring
a successful exit and **exactly one Unity-version token equal to
`6000.3.18f1`**. The configured `ProjectVersion.txt` must match as well.
An executable from a different Unity release cannot satisfy acceptance
merely because it was supplied using `-EditorPath` or has a plausible
filename. The evidence manifest records `actual_editor_version` separately
from the configured project version. CI tests this with temporary fake
executables, rejecting wrong, ambiguous, missing or failed version probes;
that synthetic check is **not a real Unity run**.

The gate writes a **new, local-only** `Logs/unity-acceptance.json` only after
all four actual validations succeed. The ignored `Logs/` folder contains
Editor smoke, Play Mode, build and Windows Player startup logs plus NUnit XML;
the manifest records the tested Git HEAD, generated scene SHA-256, configured
Editor version, test count, executable SHA-256, and SHA-256 for each log/result
file. The Windows Player smoke requires a clean exit code and a runtime marker
written only after the actual packaged Player boots its procedural
director, movement motor, follow camera, guard, collider-backed vehicle,
physical cash and courier presenters, HUD, original generated audio and
all 21 unique interaction station actions. The same probe also writes,
reloads, atomically replaces and reloads a **real isolated checkpoint**,
checking a lawful courier delivery, clean bank balance and the previous
backup checkpoint. A missing/invalid replacement or missing backup fails
the smoke rather than producing a green marker.

The built Player is launched in `-batchmode -nographics` using an opt-in
`-rabronPlayerSmoke` flag, with a finite timeout and a fresh `-logFile`.
The smoke invocation first confirms it is writing inside a unique
`rabron-player-smoke` subdirectory of Unity's temporary cache. It refuses
any other save location and only removes that verified invocation directory
afterward; it **never writes or removes normal demo checkpoints**. This
automated **headless** startup and persistence probe is
**not a manual** or visually rendered gameplay test; it cannot validate
graphics, camera interaction, human controls, real vehicle feel or windowed
performance. A timeout, crash, missing marker or missing log rejects the
entire acceptance manifest. Unity's supported standalone command flags
are documented at
https://docs.unity.com/en-us/engine/6000.3/manual/unity-editor/command-line-arguments/player.
This is **not a real Unity run in hosted CI**, and Git HEAD alone does not
fingerprint the machine's Unity-generated scene, settings or installed packages.
No original game resources are copied into the manifest.

A prior acceptance manifest is **deleted before every attempt**, including
a failed attempt. The Git HEAD captured at the start is checked again at the
source-provenance boundaries before Editor smoke, after the Editor smoke, and
after the Windows build/Player run. A changed Git HEAD **rejects local Unity
acceptance** even if the newly checked-out tree is clean: the manifest must
never attribute one revision's work to another. If Unity modifies tracked
source or settings while importing, inspect and commit those changes, rerun
from a clean revision, and do not treat the failed attempt as accepted.
The synthetic CI gate verifies acceptance of the actual matching Git HEAD
and rejection of a deliberately mismatched 40-character SHA, **without
changing branches or launching Unity**. It also rejects a missing Unity
installation and stale green manifest; this is **not a real Unity run**.

The synthetic provenance test in CI creates/removes temporary dummy
`.cs`, alternate `.unity`, allowed `.meta`, known generated scene, package
manifest-like JSON, project setting, editor tool and linked core source files.
It requires the preflight to reject every untracked code/configuration input
outside the permitted Unity import outputs. This is **not a real Unity run**;
it neither launches Unity nor validates real project contents on a Windows
workstation.

The manifest is local and can contain a machine-specific Unity installation
path. Do not publish the raw log files or manifest without checking them for
machine names, local directories, license identifiers or other personal data.
Even a successful manifest establishes only **automated local validation**.
Manual rendered-player checks—keyboard/gamepad input, jumping/ceiling,
camera collision, physical pickup/return/delivery, banking, save/restart and
interactively launching the Windows EXE—remain required before closing
playable acceptance issue #9.

## Real Unity Play Mode acceptance (Windows)

The prototype now includes three Unity Test Framework Play Mode acceptance
tests (two gameplay paths and one isolated save-recovery regression). They
run **inside Unity** and are not simulated by the Python/.NET
CI pipelines:

- Runtime bootstrap: live director, player controller, camera, UI Toolkit
  HUD, guard, cash presenter (including its intentionally inactive zero-cash
  state) and 21 station markers
- Full gameplay dispatcher: scout, mask, robbery, guard control, loot,
  escape, sell, physical counter pickup, laundering, city exit and return,
  bank deposit and next-heist reset
- Save-corruption recovery: an isolated batch-only NUnit case deliberately
  makes primary and backup unreadable, confirms autosave leaves their bytes
  unchanged and keeps the persistent warning visible, then verifies recovery
  from a valid backup without reading the player's normal save

The dispatcher test also checks courier pickup, no-payout return,
parcel visibility on the player, save/restore, delivery and banking.
Both paths call the production dispatcher directly via reflection.
The physical counter cash starts hidden at zero, so the Play Mode test
discovers its presenter with Unity's include-inactive query and then checks
the visible-on-fence/hidden-after-collection transitions without enabling
the object merely for discovery. This behavior is **source-authored, not a
completed Unity test run**. Manual WASD/gamepad controls, live physics
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
process exit, passing NUnit result, **at least three passed cases**,
zero failed/skipped cases, and **all three named acceptance methods**,
including `UnreadableCheckpointsMustSurviveLaterAutosaves`. A green-looking
two-case report, or a third unrelated passing test substituted for save
recovery, now **fails closed**; zero-test runs also fail.

During command-line `-runTests` Unity test runs, demo checkpoints use
an isolated **per-invocation** folder under
`Application.temporaryCachePath/rabron-playmode-tests/<random-run-id>/`,
rather than the developer's normal save. The random folder is generated
once per loaded Editor domain and remains stable for all checkpoint reads,
atomic writes and backups in that run; the following test invocation receives
a different folder and cannot inherit an earlier run's arrest, courier or
bank state. Temporary Unity test files may remain in the OS cache until
removed by normal cache cleanup, but they are not player progress. Regular
Editor Play Mode and Windows EXE sessions still use
`Application.persistentDataPath`. The isolation assertion specifically
checks command-line `-runTests` invocations; GUI test runs are not covered
by this batch-mode condition.

Source-level CI only syntax-lints the PowerShell runner and checks structural
test coverage; it **does not** execute Unity. A real NUnit report is needed
before reporting an actual Play Mode pass.

Unity reference:
https://docs.unity.com/en-us/engine/6000.3/manual/programming-environment/test-framework-introduction/running-tests/run-tests-from-command-line

## Local progress saving

The local **demo** now retains the authoritative gameplay session between
Play Mode sessions and Windows executable launches. On startup it loads a
versioned checkpoint from Unity's \`Application.persistentDataPath\`.
Successful interactions, guard alarms, completed laundering, application
pause and quit trigger saves. You can stop during a heist, with uncollected
fence money, a pending civilian courier parcel, or while a laundering timer is running, then resume without
minting extra currency. A timer that expired while the app was closed
completes on the next gameplay update.

The file is \`rabron-prototype-v1.json\` with a \`.bak\` previous checkpoint.
The app saves via a staged `.tmp` file and replacement, preserving the earlier
version on each completed write. It validates restored roles, stages, loot,
balances, and any pending laundering payout/deadline; corrupt or unsupported
checkpoints are rejected, with a previous valid backup used if available.

If a crash interrupts the **first ever save** and neither a committed primary
nor a backup exists, a valid staged `.tmp` checkpoint is promoted into the
primary **without overwriting** anything, preserving the unfinished progress
and its exact bytes. Committed primary/backup saves still take priority over
staged data. An invalid orphan `.tmp` is **preserved, not overwritten**, with
autosave disabled; if primary or backup is damaged, even a valid staged file
cannot bypass corrupt-file protection. Copy **all** files, including any stage,
to safety for manual recovery. If staged promotion itself fails, the state
recovers in memory but saves stay disabled so the staged bytes survive.
These are authored real Unity Play Mode filesystem regressions, **not executed**
by hosted GitHub CI.

When a valid primary or backup is already present, a leftover `.tmp` might
contain **uncommitted, more recent** progress from a later interrupted write.
The committed checkpoint still wins on loading, but the next autosave moves
the leftover staged file into a uniquely named `.tmp.staged-<random-id>`
sibling **before** writing its own stage. This preserves the old bytes for
manual recovery rather than silently overwriting them. Preserve these files
when backing up local progress; they are not automatically replayed, and a
failed preservation move makes the attempted save fail rather than replacing
the old stage. The isolated real Unity Play Mode scenario for this behavior is
authored but **not executed** in hosted CI.

If the backup is valid but the primary is unreadable, recovery first moves the
damaged primary into a unique sibling **quarantine** file named
`rabron-prototype-v1.json.corrupt-<random-id>`, then copies the validated
backup into the now-vacant primary path **without overwriting** anything.
This preserves the damaged file's original bytes for potential manual recovery
instead of silently erasing them. The quarantine is not auto-deleted; store it
safely if investigating lost progress. If either the quarantine move or copy
fails, the game may resume from backup in memory but **autosave stays disabled**
so that the validated backup cannot be lost during save rotation.

A valid primary can also coexist with an **unreadable backup**. Before the next
successful autosave replaces the backup, the old unreadable `.bak` is moved
to a unique `.bak.corrupt-<random-id>` sibling without overwriting anything.
The normal rotation then stores the previously valid primary as the new
backup. If the damaged-backup move fails, the attempted save fails instead
of destroying those bytes; the existing persistent write-error warning
remains active until a successful save. These filesystem cases are covered
by an authored isolated Unity Play Mode regression, **not executed** by
hosted CI. Preserve quarantine files when collecting local recovery data.
If **both** save and backup are unreadable, the demo starts a fresh in-memory
session but **autosave is disabled** to avoid overwriting the damaged files.
Copy or move the save and backup files to a safe location, then restart the
game to enable a new checkpoint; do not continue expecting this temporary
session to be saved. If a good backup is loaded but cannot be copied back to
the primary path, saves are also paused so the remaining valid backup is
not overwritten. The HUD shows a **persistent SAVING DISABLED warning** at the top of the
gameplay panel for the entire unsaved session, regardless of temporary
interaction notices; it warns that new progress will not be kept. A successful
new load of a valid checkpoint clears it. The warning does not reveal the
user's filesystem paths. The HUD also reports the immediate save failure
rather than silently discarding potential recovery data.

Ordinary **failed disk writes** (full storage, denied file permissions or a
blocked temporary write path) do **not** mean that an otherwise valid saved
checkpoint is corrupt. They instead show a persistent **LAST SAVE FAILED**
banner while the game is running, warning that recent progress may be lost.
Other notifications, including laundering completion, guard alarm and
arrest, cannot mask this warning. The immediate save-error notice also wins
over the normal success, alarm or custody text when those transitions fail to
write a checkpoint; the full disk error remains visible briefly while the
persistent banner remains until a confirmed write. Check free space and
folder permissions and retry a normal interaction/checkpoint; only a
confirmed successful write clears the banner.
Do not quit assuming the latest action was persisted. The existing valid
primary/backup files remain protected when a write fails. The real Unity Play
Mode save test deliberately occupies its isolated `.tmp` path with a
directory to exercise this rejection and successful recovery; hosted
Python/.NET source audits do not execute that filesystem test inside Unity.
No game binaries or personal account credentials are stored.

To start a clean demo, **close Play Mode/the game**, then remove both
\`rabron-prototype-v1.json\` and \`rabron-prototype-v1.json.bak\`
inside Unity's persistent data directory. This is a **local-only prototype
checkpoint**, not the original game's server save, multiplayer account,
seven-day wipe, or protected bank ledger. Only gameplay state is saved;
the character respawns at the city start (or the desert return marker
when outside the city), not at the previous exact coordinate.

The batch-only Unity Play Mode test writes intentionally invalid checkpoint
files **inside the isolated per-invocation test directory**, confirms that
subsequent autosave does not alter either file, and checks that a valid backup
can be loaded and saved again. It skips GUI test sessions to avoid touching
normal player saves; actual Unity execution is still required.

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
| Hold crouch (on foot) | Left Ctrl | Right-stick click |
| Jump (grounded only) | Space | North face button (Y / Triangle) |
| Interact at a highlighted pillar | E | South face button (A) |
| Enter/exit the parked practice car | E (exit only when stopped) | South face button (A) |
| Drive forward / reverse | W / S | Left stick up / down |
| Steer while driving | A / D | Left stick left / right |
| Brake while driving | Space | North face button (Y / Triangle) |
| Release mouse cursor | Escape | — |
| Lock cursor again | Left click in the Game view | — |

**Gamepad right stick stays active when the mouse cursor is unlocked** with
Escape, on foot and while driving. Unlocking disables only mouse-driven camera
movement; left click in the Game view recaptures mouse look. The gamepad
does not require a mouse or a left click for camera movement.

The independently authored motor uses a provisional jump height and gravity.
Jumping requires ground contact and cancels upward velocity when the player
hits a ceiling. The north-face gamepad button was selected to retain the
existing south-face interact control. Hold **Left Ctrl / right-stick click**
to crouch on foot with a shorter physical collision capsule, slower walking
and a lower camera. Releasing crouch restores standing only when the upper
capsule has enough nontrigger headroom; a low ceiling leaves the player
crouched until a clear space is reached. Sprint cannot override crouched
speed. Air jumping and vaulting are not implemented. The movement, crouch
clearance and camera must still be manually validated in a real Unity Editor
and Windows build.

## Original practice car (no vehicle economy)

A single **driveable practice car** is parked to the east of the starting
road, with a gold **Enter practice car** marker on its side. Approach it
as a **Civilian** in **Idle** with no courier cargo and press E / gamepad A.
The actor's walking collider and visual are hidden while boarded; the same
third-person camera follows the car. W/S and left-stick throttle drive forward
or reverse, A/D and the stick steer, and Space/Y brakes. **Mouse and right stick
look around independently while driving**: camera yaw orbits relative to the
car's heading without steering it, with the same limited pitch as on foot.
Gamepad look remains available even after Escape unlocks the mouse cursor.
Once nearly stopped, **release and press E / A again on a later frame** to exit
on a collision-clear side. The driving camera orbit resets on boarding and
exiting; after a safe exit the walking heading matches the parked car.
The boarding press is not also an exit press, regardless of Unity's
component Update order; this protects against an immediate **same-frame**
enter/exit input race. If both sides are blocked or the car is moving too
quickly, exit is refused instead of placing the avatar inside a wall.
The exit clearance uses the walking avatar's **full CharacterController
capsule**, including its lower section and skin-width margin, so ankle-height
obstacles cannot be ignored by a high-only collision probe. It also uses a swept capsule query along the full passenger path
from the parked car to each otherwise-clear landing point: a
solid wall *between* the door and landing cannot be bypassed by teleporting
through it. Nontrigger geometry blocks the swept path, both queries fail
closed on overflow, and the car/driver themselves are ignored. If one side
is blocked, the other may still be used. No cash is paid for entering,
driving or exiting.

This uses an invented, low-speed **CharacterController** car with a simple
original cube body and wheels. It is not a professional wheel/suspension
simulation, model extracted from the reference game, AI traffic system or
server-authoritative drive. **Vehicle position resets on restart**; normal
player banking, courier and heist saves are unaffected. The car cannot carry
an active courier parcel and does not transfer gameplay role or money. Real
keyboard/gamepad steering, obstacles, exit clearance and a Windows executable
must still be checked in Unity 6000.3; the hosted Python/.NET CI has not
driven the car.

## Civilian courier alternative (no robbery)

The original, independently authored demo also offers a lawful, repeatable
route for players who prefer not to join the criminal heist:

1. From the starting street, walk to the western **Courier dispatch** kiosk
   (near the ATM) and interact with **Collect legal delivery parcel**.
2. The parcel appears as a small box on your character and is remembered by
   the versioned checkpoint. You cannot scout, wear the criminal mask or
   leave the city while a delivery is active. To abandon the task, return
   to the western dispatch kiosk and interact with **Return parcel without
   payment**. The box disappears, no clean cash is awarded, and the heist
   path is immediately available again.
3. Cross to the eastern **Courier recipient** kiosk and interact with
   **Deliver legal parcel**. The configured demo quote credits **clean
   cash** once; repeating the delivery without another pickup cannot pay
   twice. No loot, dirty cash, fence or laundering are involved.
4. Open a bank account as a civilian at the ATM and deposit clean cash.
   You can start another delivery or scout the heist afterward.

The initial demonstration courier reward is **35 invented demo units**,
configured in the existing `PrototypeBalance` ScriptableObject. This is a
named local legal-job cash source, **not an original game reward formula, a
server-authorized transaction or an anti-cheat system**. Earlier v1 saves
without the optional parcel flag load with no parcel. The demo intentionally
permits only one courier parcel at a time; a dedicated station is the
no-payout return marker. The parcel mesh is presentation-only and its collider
is disabled. The courier route contains no vehicle cargo logistics,
item weight, routing algorithm or mission generator.

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
   If the alarm is active and you approach the still-active guard within
   the small demo arrest radius while visible, the guard arrests you:
   unsold loot and dirty cash are confiscated. Your legitimate clean cash
   and bank balance remain intact. The game warps you to the simple
   **police custody** desk in the southern district. Interact with the
   **Leave police custody** marker to return as a civilian and restart.
   This needs a **new press of E / gamepad A after arrival**: an interaction
   pressed before the automatic arrest cannot release custody on the same
   frame. Alternatively, evade the guard and collect one or both loot objects.
5. Leave the building; use the **Escape** pillar on the road **after
   collecting at least one loot item**. If you choose not to take anything,
   use the neighboring **Withdraw from heist without payment** pillar
   instead. This returns you to civilian/idle with **no reward** and no
   change to existing account or cash balances; it clears the heist alarm
   and guard status so you may scout another attempt or take a courier job.
   The guard can still arrest you if you stay visible nearby during an alarm.
6. Go **west** to the fence counter. Selling now reveals four original
   green cash-bundle meshes **on top of the counter**; they are visual only,
   with no collision. None of the cash is added to your wallet yet.
7. Walk around the counter to its collection marker and press **E / A**.
   The bundle meshes disappear and the balance moves from Counter Cash to
   Dirty Cash. The next destination is the **eastern** laundry workstation.
8. Laundering finishes after an adjustable demo timer. Go **south** to the
   city-exit marker to clear criminal status. While outside the city, the HUD
   explicitly says **RETURN TO CITY**: use the nearby purple return marker
   at the southern road before looking for banking or NEXT HEIST stations.
   Those city-only markers are unavailable in the desert. The live Unity
   exit marker is only available after laundering completes.
   The independent core additionally permits travel during Idle or Scouted
   phases for compatible non-robbery paths, but never during an in-progress
   robbery, unsold fence payout, uncollected counter cash, dirty-cash
   collection, active laundering or custody. Former hand-authored Desert
   checkpoints containing unfinished heist phases are rejected on load
   rather than silently moving loot or laundering jobs across the zone
   boundary; no reward or save migration is invented.
9. As a **civilian**, open the bank account at the ATM if not already open,
   and deposit clean cash. A nearby new-heist station resets just the
   heist phase and retains account balances. Both the actual station and
   the portable gameplay core now require **civilian status inside the city**
   before resetting; laundering alone never lets a masked criminal start
   another cycle without the city-exit status clear.

The prototype has one stationary guard **placeholder** whose line-of-sight
sensor raises an alarm when the player is seen. If the guard subsequently
spots the nearby criminal while still active, it triggers the **invented
single-player custody outcome**; release has no fee or duration. Physical
overlap with the guard's trigger mesh is **not** a blind spot: at near-zero
distance, the guard ignores the undefined facing angle but still applies
any meaningful wall-occlusion check, allowing an active guard to arrest
an overlapping criminal after an alarm. Ordinary positions retain the
original limited field-of-view cone. Controlling the guard prevents
subsequent detection but cannot erase an existing alarm.

The demo guard's physical ray now aims at the player's actual upper capsule
rather than a fixed standing-height point. The procedural warehouse includes
a **solid 1.5m-high wooden cover barrier** on the central approach between the
entrance and guard. Use **Left Ctrl** or **right stick press** to crouch behind
it; standing exposes the player, and walking around either side restores the
guard's sightline while leaving routes to loot and the **guard-control marker**
just behind the barrier's left side. That marker is within actual interaction
range from the approach just left of center, although crouching blocks the
interaction ray across the cover. Standing restores the reach but can expose
you to the guard's alarm. The **near left flank** beside the barricade
still lies inside the guard's forward detection cone; it is a loud approach,
not a guaranteed silent one. For a provisional quiet option, take the
**wider left flank** inside the warehouse (about 3.6m left of the guard and
2m toward the entrance). From there the control marker is still within
interaction range and physically unobstructed but outside the guard's 55°
field of view. Use the marker to control the guard before exposing yourself.
This is an original prototype tactic, not reconstructed source-game AI.
Authored real Unity Editor geometry smoke and a Unity Play Mode test now
check the actual guard sensor, station picker, real control action and
absence of alarm on this path, but they have **not executed** in hosted CI.
You can **crouch behind low cover** to obstruct line of sight, but this is
not a magical invisibility toggle, and unblocked sightlines can still trigger
the alarm. The provisional sight range also includes vertical separation,
rather than allowing detection far above the guard. A real Unity Editor
geometry smoke scenario (standing, crouched, standing again, elevated) is
authored but **not executed** in hosted CI. Actual stealth/collision feel
requires hands-on Unity and Windows testing.

This is **not** the original NPC AI, arrest formula, police dispatch,
wanted-level system or any authoritative online gameplay. Police patrol
movement, pursuit and server enforcement are not implemented.

### Physical access and camera

Nearby pillars now require a clear ray from the player's actual upper
body capsule: a solid warehouse wall or fence counter prevents interaction
from its opposite side. **Crouched station interactions** also respect the
lowered capsule, so the waist-high warehouse cover blocks attempts to reach
the guard-control marker through it. Stand up or walk around the obstacle
before interacting; guard sight and station targeting use the same physical
point. A Unity Editor geometry regression using the generated barrier and
real marker is authored but **not executed** in hosted CI.
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
- Civilian courier completion reward: 35 demo units (credited as clean cash)

To override them, in Unity use **Assets > Create > Rabron > Prototype Economy**,
configure the ScriptableObject in the Inspector, and save it as
\`Assets/Resources/DemoEconomy.asset\`. The runtime loads it automatically.
No hard-coded economic rates live in the portable \`HeistSession\` core.

The demo's clean payout uses **overflow-safe integer arithmetic**:
`floor(dirtyAmount × percent / 100)`. It correctly handles a positive
`long.MaxValue` dirty balance at 80% or 100% without floating point,
silent clamping or a changed exchange rate. A configured percentage outside
0–100 is rejected even if set programmatically rather than in the Inspector.
A real Unity Editor smoke scenario is authored for boundary values but
**not yet executed** in hosted CI; these figures are not original-game rates.
The core also prevents **unpayable laundering jobs** when the promised clean
payout would exceed the remaining wallet capacity. It rejects the offer
before consuming dirty cash and refuses impossible pending jobs on save
restore. This is a local-demo safety rule, not a reference-game mechanic;
its Unity JSON smoke scenario is authored but not executed in hosted CI.

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

GitHub Actions checks the referenced local package, all 17 interaction targets,
versioned save adapters and invariant validation,
Unity project manifest, demo bootstrapping and code separation. The original
.NET console tests compile and exercise money conservation and phase gating.
**Neither test substitutes for opening the actual project in Unity Editor.**

Still missing: a real Unity Editor scene/build smoke test; exported Windows EXE;
police dispatch, mobile guard AI, human multiplayer, base building,
full vehicle ownership/traffic, cargo,
clans, prison, persistent server state, realistic art or animations; measured
matching heist payouts, loot tables, laundering ratios and timers. The logic
uses provisional restrictions and is **not claimed to match ROB RUN exactly**.

The shipped original Unity player files are only evidence, not redistributed
game assets. Do not publish the original game resources without rights.

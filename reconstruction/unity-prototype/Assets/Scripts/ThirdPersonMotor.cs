using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.InputSystem;

namespace Rabron.Prototype
{
    /// <summary>Third-person motor driven by Unity's current Input System.</summary>
    [RequireComponent(typeof(CharacterController))]
    public sealed class ThirdPersonMotor : MonoBehaviour
    {
        private CharacterController _character = null!;
        private Camera _camera = null!;
        private InputAction _move = null!;
        private InputAction _mouse = null!;
        private InputAction _stick = null!;
        private InputAction _sprint = null!;
        private InputAction _interact = null!;
        private InputAction _jump = null!;
        private InputAction _crouch = null!;
        private const float DemoGravity = 20f;
        private const float DemoJumpHeight = 1.15f;
        private const float DemoCrouchHeight = 1.15f;
        private const float DemoCrouchSpeed = 2.4f;
        private float _standingHeight;
        private float _crouchHeight;
        private float _standingStepOffset;
        private Vector3 _standingCenter;
        private Transform? _bodyVisual;
        private Vector3 _standingVisualPosition;
        private Vector3 _standingVisualScale;
        private bool _isCrouched;
        private float _pitch = 18f;
        private float _drivingLookYaw;
        private float _verticalVelocity;
        private PrototypeVehicle? _vehicle;
        private readonly List<Renderer> _hiddenRenderers = new List<Renderer>();
        private readonly RaycastHit[] _cameraHits = new RaycastHit[24];
        private readonly Collider[] _standHits = new Collider[32];
        private int _exitInteractFrame = -1;
        private int _boardedVehicleFrame = -1;

        // Both director and motor consume the same press in Update, whose
        // relative execution order is unspecified. Only a fresh later-frame
        // press may leave the newly boarded car.
        private static bool ExitPressAfterBoard(int boardFrame, int frame, bool pressed)
            => pressed && boardFrame != frame;

        public bool IsDriving => _vehicle != null;
        public bool IsCrouched => _isCrouched;
        public bool InteractPressed => _vehicle == null && _interact != null &&
            _exitInteractFrame != Time.frameCount && _interact.WasPressedThisFrame();

        public void BoardVehicle(PrototypeVehicle vehicle)
        {
            if (_vehicle != null || vehicle == null || !vehicle.BeginDriving())
                throw new InvalidOperationException("Car is already occupied.");

            _vehicle = vehicle;
            _drivingLookYaw = 0f;
            _boardedVehicleFrame = Time.frameCount;
            _character.enabled = false;
            foreach (Renderer visual in GetComponentsInChildren<Renderer>(true))
            {
                if (!visual.enabled)
                    continue;
                visual.enabled = false;
                _hiddenRenderers.Add(visual);
            }
            transform.position = vehicle.transform.position;
        }

        public bool TryExitVehicle()
        {
            if (_vehicle == null || !_vehicle.TryFindExit(transform, out Vector3 position))
                return false;

            PrototypeVehicle parkedCar = _vehicle;
            parkedCar.EndDriving();
            _vehicle = null;
            transform.position = position;
            transform.rotation = Quaternion.Euler(0f, parkedCar.transform.eulerAngles.y, 0f);
            _drivingLookYaw = 0f;
            _verticalVelocity = 0f;
            _character.enabled = true;
            RestoreVisuals();
            _exitInteractFrame = Time.frameCount;
            return true;
        }

        private void RestoreVisuals()
        {
            foreach (Renderer visual in _hiddenRenderers)
                if (visual != null)
                    visual.enabled = true;
            _hiddenRenderers.Clear();
        }

        private void Awake()
        {
            _character = GetComponent<CharacterController>();
            _standingHeight = _character.height;
            _standingCenter = _character.center;
            _standingStepOffset = _character.stepOffset;
            _crouchHeight = Mathf.Min(DemoCrouchHeight, _standingHeight);
            _bodyVisual = transform.Find("Player mesh");
            if (_bodyVisual != null)
            {
                _standingVisualPosition = _bodyVisual.localPosition;
                _standingVisualScale = _bodyVisual.localScale;
            }
            // Editor smoke tests instantiate the procedural world outside Play Mode.
            // Do not spawn an unparented camera or capture the cursor in edit mode.
            if (!Application.isPlaying)
                return;

            _move = new InputAction("Move", InputActionType.Value);
            _move.AddCompositeBinding("2DVector")
                .With("Up", "<Keyboard>/w").With("Down", "<Keyboard>/s")
                .With("Left", "<Keyboard>/a").With("Right", "<Keyboard>/d");
            _move.AddBinding("<Gamepad>/leftStick");
            _mouse = new InputAction("Mouse Look", InputActionType.Value, "<Mouse>/delta");
            _stick = new InputAction("Gamepad Look", InputActionType.Value,
                                      "<Gamepad>/rightStick");
            _sprint = new InputAction("Sprint", InputActionType.Button);
            _sprint.AddBinding("<Keyboard>/leftShift");
            _sprint.AddBinding("<Gamepad>/leftStickPress");
            _interact = new InputAction("Interact", InputActionType.Button);
            _interact.AddBinding("<Keyboard>/e");
            _interact.AddBinding("<Gamepad>/buttonSouth");
            // Keep existing A / south-face interaction; Y / north-face jumps.
            _jump = new InputAction("Jump", InputActionType.Button);
            _jump.AddBinding("<Keyboard>/space");
            _jump.AddBinding("<Gamepad>/buttonNorth");
            // Hold crouch with a separate control from sprint or look.
            _crouch = new InputAction("Crouch", InputActionType.Button);
            _crouch.AddBinding("<Keyboard>/leftCtrl");
            _crouch.AddBinding("<Gamepad>/rightStickPress");

            var cam = new GameObject("Prototype Follow Camera");
            _camera = cam.AddComponent<Camera>();
            _camera.fieldOfView = 70f;
            _camera.nearClipPlane = 0.1f;
            cam.AddComponent<AudioListener>();
            Cursor.lockState = CursorLockMode.Locked;
            Cursor.visible = false;
        }

        private void OnEnable()
        {
            _move?.Enable();
            _mouse?.Enable();
            _stick?.Enable();
            _sprint?.Enable();
            _interact?.Enable();
            _jump?.Enable();
            _crouch?.Enable();
        }

        private void OnDisable()
        {
            _move?.Disable();
            _mouse?.Disable();
            _stick?.Disable();
            _sprint?.Disable();
            _interact?.Disable();
            _jump?.Disable();
            _crouch?.Disable();
            if (_vehicle != null)
            {
                _vehicle.EndDriving();
                _vehicle = null;
                _drivingLookYaw = 0f;
                _character.enabled = true;
                RestoreVisuals();
            }
        }

        private void OnDestroy()
        {
            _move?.Dispose();
            _mouse?.Dispose();
            _stick?.Dispose();
            _sprint?.Dispose();
            _interact?.Dispose();
            _jump?.Dispose();
            _crouch?.Dispose();
            if (_camera != null)
                Destroy(_camera.gameObject);
            if (Application.isPlaying)
            {
                Cursor.lockState = CursorLockMode.None;
                Cursor.visible = true;
            }
        }

        private void Update()
        {
            if (Keyboard.current != null && Keyboard.current.escapeKey.wasPressedThisFrame)
            {
                Cursor.lockState = CursorLockMode.None;
                Cursor.visible = true;
            }
            if (Mouse.current != null && Mouse.current.leftButton.wasPressedThisFrame)
            {
                Cursor.lockState = CursorLockMode.Locked;
                Cursor.visible = false;
            }

            // Mouse movement needs captured cursor; gamepad right-stick
            // must remain available after Escape releases it. Camera look
            // runs before the occupied-car branch and never steers the car.
            Vector2 look = ComposeLook(_mouse.ReadValue<Vector2>(),
                _stick.ReadValue<Vector2>(),
                Cursor.lockState == CursorLockMode.Locked, Time.deltaTime);
            if (look.sqrMagnitude > 0f)
                ApplyLookDelta(look);

            if (_vehicle != null)
            {
                if (ExitPressAfterBoard(_boardedVehicleFrame, Time.frameCount,
                                        _interact.WasPressedThisFrame()))
                    TryExitVehicle();
                if (_vehicle != null)
                {
                    Vector2 drive = Vector2.ClampMagnitude(_move.ReadValue<Vector2>(), 1f);
                    _vehicle.Drive(drive, _jump.IsPressed(), Time.deltaTime);
                    transform.position = _vehicle.transform.position;
                    return;
                }
            }

            UpdateCrouch(_crouch.IsPressed());
            Vector2 axis = Vector2.ClampMagnitude(_move.ReadValue<Vector2>(), 1f);
            Vector3 planar = transform.right * axis.x + transform.forward * axis.y;
            float speed = _isCrouched ? DemoCrouchSpeed :
                (_sprint.IsPressed() ? 7f : 4.5f);
            _verticalVelocity = IntegrateVertical(_verticalVelocity,
                _character.isGrounded, _jump.WasPressedThisFrame(), Time.deltaTime);
            CollisionFlags collision = _character.Move(
                (planar * speed + Vector3.up * _verticalVelocity) * Time.deltaTime);
            _verticalVelocity = ResolveCeiling(_verticalVelocity, collision);
        }

        // Pure look composition is used by runtime input and the real Unity
        // Play Mode regression. Releasing the mouse cursor must never mute
        // the gamepad right stick or redirect driving orbit into steering.
        private static Vector2 ComposeLook(Vector2 mouseDelta, Vector2 gamepadStick,
                                           bool cursorLocked, float deltaSeconds)
        {
            Vector2 mouseLook = cursorLocked ? mouseDelta * 0.12f : Vector2.zero;
            Vector2 stickLook = Vector2.ClampMagnitude(gamepadStick, 1f)
                * (120f * Mathf.Max(0f, deltaSeconds));
            return mouseLook + stickLook;
        }

        // Keep the capsule's feet at the same level when changing height.
        // Resuming full height requires real nontrigger headroom, never just
        // a button release that can clip the player through a ceiling.
        private void UpdateCrouch(bool held)
        {
            if (held == _isCrouched)
                return;
            if (!held && !CanStand())
                return;

            _isCrouched = held;
            float height = held ? _crouchHeight : _standingHeight;
            if (held)
                _character.stepOffset = Mathf.Min(_standingStepOffset, 0.3f);
            _character.height = height;
            _character.center = _standingCenter -
                Vector3.up * ((_standingHeight - height) * 0.5f);
            if (!held)
                _character.stepOffset = _standingStepOffset;

            if (_bodyVisual != null)
            {
                _bodyVisual.localPosition = _standingVisualPosition -
                    Vector3.up * ((_standingHeight - height) * 0.5f);
                Vector3 visualScale = _standingVisualScale;
                visualScale.y *= height / _standingHeight;
                _bodyVisual.localScale = visualScale;
            }
        }

        private bool CanStand()
        {
            // Test only the upper volume gained by standing, so the ground
            // underneath the player's current capsule is not an obstacle.
            float radius = _character.radius;
            float bottomY = _standingCenter.y - _standingHeight * 0.5f;
            Vector3 crouchedHead = transform.TransformPoint(
                new Vector3(_standingCenter.x,
                    bottomY + _crouchHeight - radius, _standingCenter.z));
            Vector3 standingHead = transform.TransformPoint(
                new Vector3(_standingCenter.x,
                    bottomY + _standingHeight - radius, _standingCenter.z));
            Vector3 scale = transform.lossyScale;
            float clearanceRadius = (radius + _character.skinWidth) *
                Mathf.Max(Mathf.Abs(scale.x), Mathf.Abs(scale.z));
            int count = Physics.OverlapCapsuleNonAlloc(
                crouchedHead, standingHead, clearanceRadius,
                _standHits, ~0, QueryTriggerInteraction.Ignore);
            if (count == _standHits.Length)
                return false; // Never assume clearance with truncated hits.
            for (int i = 0; i < count; i++)
            {
                Collider hit = _standHits[i];
                if (hit != null && !hit.transform.IsChildOf(transform))
                    return false;
            }
            return true;
        }

        private void ApplyLookDelta(Vector2 look)
        {
            if (_vehicle == null)
                transform.Rotate(0f, look.x, 0f);
            else
                _drivingLookYaw = Mathf.Repeat(_drivingLookYaw + look.x + 180f, 360f) - 180f;

            _pitch = Mathf.Clamp(_pitch - look.y, -45f, 70f);
        }

        // Pure steps are shared by the motor and its real Unity test source.
        // These are invented demo movement parameters, not source-game physics.
        private static float IntegrateVertical(float velocity, bool grounded,
                                                bool jumpPressed, float deltaSeconds)
        {
            if (grounded)
            {
                // Reset old ascent when touching ground; a held button is not
                // another jump without a fresh WasPressedThisFrame event.
                velocity = jumpPressed ? Mathf.Sqrt(2f * DemoGravity * DemoJumpHeight)
                                       : -2f;
            }
            return velocity - DemoGravity * deltaSeconds;
        }

        private static float ResolveCeiling(float velocity, CollisionFlags collision)
        {
            return velocity > 0f && (collision & CollisionFlags.Above) != 0
                ? 0f : velocity;
        }

        private void LateUpdate()
        {
            Transform focus = _vehicle != null ? _vehicle.transform : transform;
            Quaternion yaw = Quaternion.Euler(0f,
                focus.eulerAngles.y + (_vehicle != null ? _drivingLookYaw : 0f), 0f);
            Quaternion pitch = Quaternion.Euler(_pitch, 0f, 0f);
            Vector3 pivot = focus.position +
                Vector3.up * (_vehicle != null ? 1.6f : _isCrouched ? 1.08f : 1.6f);
            Vector3 target = pivot + yaw * pitch * new Vector3(0f, 0.9f, -5.5f);
            target = WorldOcclusion.ClampCamera(pivot, target, focus, _cameraHits);

            // Smooth only when moving away from obstacles. Moving toward a
            // blocked wall must be immediate or the camera can clip through it.
            float damping = 1f - Mathf.Exp(-12f * Time.deltaTime);
            Vector3 eased = Vector3.Lerp(_camera.transform.position, target, damping);
            _camera.transform.position = WorldOcclusion.ClampCamera(pivot, eased,
                                                                  focus, _cameraHits);
            _camera.transform.LookAt(pivot);
        }

        public void WarpTo(Vector3 destination)
        {
            _character.enabled = false;
            transform.position = destination;
            _verticalVelocity = 0f;
            _character.enabled = true;
        }
    }
}

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
        private float _pitch = 18f;
        private float _verticalVelocity;
        private readonly RaycastHit[] _cameraHits = new RaycastHit[24];

        public bool InteractPressed => _interact != null && _interact.WasPressedThisFrame();

        private void Awake()
        {
            _character = GetComponent<CharacterController>();
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
        }

        private void OnDisable()
        {
            _move?.Disable();
            _mouse?.Disable();
            _stick?.Disable();
            _sprint?.Disable();
            _interact?.Disable();
        }

        private void OnDestroy()
        {
            _move?.Dispose();
            _mouse?.Dispose();
            _stick?.Dispose();
            _sprint?.Dispose();
            _interact?.Dispose();
            if (_camera != null)
                Destroy(_camera.gameObject);
            Cursor.lockState = CursorLockMode.None;
            Cursor.visible = true;
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

            if (Cursor.lockState == CursorLockMode.Locked)
            {
                Vector2 look = _mouse.ReadValue<Vector2>() * 0.12f
                    + _stick.ReadValue<Vector2>() * (120f * Time.deltaTime);
                transform.Rotate(0f, look.x, 0f);
                _pitch = Mathf.Clamp(_pitch - look.y, -45f, 70f);
            }

            Vector2 axis = Vector2.ClampMagnitude(_move.ReadValue<Vector2>(), 1f);
            Vector3 planar = transform.right * axis.x + transform.forward * axis.y;
            float speed = _sprint.IsPressed() ? 7f : 4.5f;
            _verticalVelocity = _character.isGrounded
                ? -2f : _verticalVelocity - 20f * Time.deltaTime;
            _character.Move((planar * speed + Vector3.up * _verticalVelocity)
                            * Time.deltaTime);
        }

        private void LateUpdate()
        {
            Quaternion yaw = Quaternion.Euler(0f, transform.eulerAngles.y, 0f);
            Quaternion pitch = Quaternion.Euler(_pitch, 0f, 0f);
            Vector3 pivot = transform.position + Vector3.up * 1.6f;
            Vector3 target = pivot + yaw * pitch * new Vector3(0f, 0.9f, -5.5f);
            target = WorldOcclusion.ClampCamera(pivot, target, transform, _cameraHits);

            // Smooth only when moving away from obstacles. Moving toward a
            // blocked wall must be immediate or the camera can clip through it.
            float damping = 1f - Mathf.Exp(-12f * Time.deltaTime);
            Vector3 eased = Vector3.Lerp(_camera.transform.position, target, damping);
            _camera.transform.position = WorldOcclusion.ClampCamera(pivot, eased,
                                                                  transform, _cameraHits);
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

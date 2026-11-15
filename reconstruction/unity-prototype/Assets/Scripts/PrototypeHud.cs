using Rabron.Reconstruction;
using UnityEngine;
using UnityEngine.UIElements;

namespace Rabron.Prototype
{
    /// <summary>Runtime UI Toolkit HUD; no UXML, textures, or external UI assets.</summary>
    public sealed class PrototypeHud : MonoBehaviour
    {
        private UIDocument _document = null!;
        private PanelSettings _settings = null!;
        private Label _state = null!;
        private Label _money = null!;
        private Label _objective = null!;
        private Label _saveWarning = null!;
        public bool SaveWarningVisible { get; private set; }
        private Label _prompt = null!;
        private Label _notice = null!;

        public void Initialize()
        {
            _settings = ScriptableObject.CreateInstance<PanelSettings>();
            _settings.scaleMode = PanelScaleMode.ConstantPixelSize;
            _settings.sortingOrder = 100f;

            _document = gameObject.AddComponent<UIDocument>();
            _document.panelSettings = _settings;

            var root = _document.rootVisualElement;
            root.pickingMode = PickingMode.Ignore;
            root.style.flexGrow = 1;

            var details = new VisualElement();
            details.pickingMode = PickingMode.Ignore;
            details.style.position = Position.Absolute;
            details.style.left = 20;
            details.style.top = 20;
            details.style.width = 465;
            details.style.paddingTop = 14;
            details.style.paddingBottom = 14;
            details.style.paddingLeft = 18;
            details.style.paddingRight = 18;
            details.style.backgroundColor = new Color(0.035f, 0.065f, 0.1f, 0.88f);
            details.style.borderTopLeftRadius = 12;
            details.style.borderTopRightRadius = 12;
            details.style.borderBottomLeftRadius = 12;
            details.style.borderBottomRightRadius = 12;
            root.Add(details);

            Add(details, "RABRON — RECONSTRUCTION PROTOTYPE", 17, true);
            Add(details, "Original blockout • invented demo balance, not source formulas",
                12, false);
            _saveWarning = Add(details, "", 15, true);
            _saveWarning.style.display = DisplayStyle.None;
            _saveWarning.style.color = new Color(1f, 0.66f, 0.47f);
            _saveWarning.style.backgroundColor = new Color(0.35f, 0.07f, 0.05f, 0.94f);
            _saveWarning.style.paddingTop = 9;
            _saveWarning.style.paddingBottom = 9;
            _saveWarning.style.paddingLeft = 10;
            _saveWarning.style.paddingRight = 10;
            _state = Add(details, "", 15, true);
            _money = Add(details, "", 14, false);
            _objective = Add(details, "", 15, false);

            _notice = Add(root, "", 17, true);
            _notice.style.position = Position.Absolute;
            _notice.style.left = 20;
            _notice.style.bottom = 115;
            _notice.style.width = 610;
            _notice.style.color = new Color(1f, 0.78f, 0.43f);
            _notice.style.backgroundColor = new Color(0.04f, 0.07f, 0.1f, 0.75f);

            _prompt = Add(root, "", 21, true);
            _prompt.style.position = Position.Absolute;
            _prompt.style.left = 0;
            _prompt.style.right = 0;
            _prompt.style.bottom = 36;
            _prompt.style.unityTextAlign = TextAnchor.MiddleCenter;
            _prompt.style.color = new Color(0.95f, 0.97f, 1f);
            _prompt.style.backgroundColor = new Color(0.04f, 0.07f, 0.1f, 0.8f);

            Add(details, "WASD / left stick: move  •  Mouse / right stick: look", 12, false);
            Add(details, "Shift / stick-click: sprint  •  Space / Y: jump", 12, false);
            Add(details, "E / A: interact  •  Esc: cursor", 12, false);
        }

        public void Render(HeistSession state, string objective, string prompt,
                           string message, bool savingDisabled)
        {
            // The normal notice expires after 4.5 seconds; unsafe save state
            // must remain visible until a new valid session is loaded.
            SaveWarningVisible = savingDisabled;
            _saveWarning.style.display = savingDisabled ? DisplayStyle.Flex : DisplayStyle.None;
            _saveWarning.text = savingDisabled
                ? "SAVING DISABLED — THIS SESSION WILL NOT BE SAVED. " +
                  "Copy or move damaged save and .bak files to safety, then restart."
                : "";
            _state.text = "Role: " + state.CurrentRole
                          + "   |   Zone: " + state.CurrentZone
                          + "   |   Stage: " + state.Phase;
            _money.text = "Counter " + state.CounterCash
                          + "   Dirty " + state.DirtyCash
                          + "   Clean " + state.CleanCash
                          + "   Bank " + state.BankBalance
                          + "\nLoot carried: " + state.Loot.Count
                          + "   Alarm: " + (state.AlarmRaised ? "TRIGGERED" : "Quiet")
                          + "   Guard: " + (state.StaffControlled ? "Controlled" : "Active")
                          + "\nCourier: " + (state.CarryingCourierParcel ? "PARCEL IN TRANSIT" : "no parcel");
            _objective.text = "OBJECTIVE\n" + objective;
            _prompt.text = string.IsNullOrEmpty(prompt)
                ? "Find the highlighted world markers" : "E / A — " + prompt;
            _notice.text = message;
        }

        private static Label Add(VisualElement parent, string text,
                                 int size, bool strong)
        {
            var label = new Label(text);
            label.pickingMode = PickingMode.Ignore;
            label.style.fontSize = size;
            label.style.marginBottom = 9;
            label.style.whiteSpace = WhiteSpace.Normal;
            label.style.color = new Color(0.92f, 0.94f, 0.96f);
            label.style.unityFontStyleAndWeight =
                strong ? FontStyle.Bold : FontStyle.Normal;
            parent.Add(label);
            return label;
        }

        private void OnDestroy()
        {
            if (_settings != null)
                Destroy(_settings);
        }
    }
}

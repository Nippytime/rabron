using UnityEngine;

namespace Rabron.Prototype
{
    public enum StationAction
    {
        Scout, Mask, BeginRobbery, Artwork, Watch, ControlStaff, Escape, Fence,
        CollectCash, Launder, ExitCity, EnterCity, OpenBank, Deposit, Reset,
        CourierPickup, CourierDropoff, CourierCancel, ReleaseCustody
    }

    /// <summary>Visible interaction target; state and finance live in HeistSession.</summary>
    public sealed class InteractionMarker : MonoBehaviour
    {
        public StationAction Action { get; private set; }
        public string Label { get; private set; } = "";

        public void Configure(StationAction action, string label)
        {
            Action = action;
            Label = label;
            name = action + " — " + label;
        }
    }
}

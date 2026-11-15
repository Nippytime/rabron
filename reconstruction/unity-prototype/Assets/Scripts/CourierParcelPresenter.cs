using UnityEngine;

namespace Rabron.Prototype
{
    /// <summary>
    /// Visual-only cargo state. No money or delivery status lives in this
    /// component; PrototypeDirector reads HeistSession every frame.
    /// </summary>
    public sealed class CourierParcelPresenter : MonoBehaviour
    {
        public bool IsVisible => gameObject.activeSelf;

        public void SetCarrying(bool carrying)
        {
            if (gameObject.activeSelf != carrying)
                gameObject.SetActive(carrying);
        }
    }
}

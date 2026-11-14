using System;
using UnityEngine;

namespace Rabron.Prototype
{
    /// <summary>
    /// Visual-only representation of cash physically waiting at the fence.
    /// The authoritative balance remains HeistSession.CounterCash.
    /// </summary>
    public sealed class CashPilePresenter : MonoBehaviour
    {
        public bool IsVisible => gameObject.activeSelf;

        public void SetAmount(long counterCash)
        {
            if (counterCash < 0)
                throw new ArgumentOutOfRangeException(nameof(counterCash));

            bool visible = counterCash > 0;
            if (gameObject.activeSelf != visible)
                gameObject.SetActive(visible);
        }
    }
}

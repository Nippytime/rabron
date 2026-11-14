using System;
using System.Collections.Generic;
using System.Linq;
using Rabron.Reconstruction;
using UnityEngine;

namespace Rabron.Prototype
{
    /// <summary>Thin Unity adapter. Only HeistSession mutates game/economy state.</summary>
    public sealed class PrototypeDirector : MonoBehaviour
    {
        private const float InteractionRadius = 3.8f;
        private HeistSession _session = null!;
        private PrototypeBalance _balance = null!;
        private ThirdPersonMotor _player = null!;
        private PrototypeHud _hud = null!;
        private IReadOnlyList<InteractionMarker> _stations = null!;
        private string _notice = "";
        private float _noticeUntil;
        private bool _ownsBalance;

        private void Awake()
        {
            _balance = Resources.Load<PrototypeBalance>("DemoEconomy");
            if (_balance == null)
            {
                _balance = ScriptableObject.CreateInstance<PrototypeBalance>();
                _ownsBalance = true;
            }

            _session = new HeistSession();
            _stations = PrototypeWorld.Create(transform, out _player);

            var hudObject = new GameObject("Prototype HUD");
            hudObject.transform.SetParent(transform, false);
            _hud = hudObject.AddComponent<PrototypeHud>();
            _hud.Initialize();
            Notice("Demo: follow the objective and approach a colored pillar.");
        }

        private void Update()
        {
            long now = DateTimeOffset.UtcNow.ToUnixTimeSeconds();
            if (_session.Phase == HeistPhase.Laundering &&
                _session.LaunderingReadyAt <= now)
            {
                _session.CompleteLaundering(now);
                Notice("Laundering complete. Leave the city to clear criminal status.");
            }

            var focused = FindNearbyStation();
            if (_player.InteractPressed)
            {
                if (focused == null)
                    Notice("Get closer to an available station.");
                else
                {
                    try
                    {
                        Perform(focused, now);
                        Notice("Completed: " + focused.Label);
                    }
                    catch (Exception error) when (error is InvalidOperationException ||
                                                  error is ArgumentException ||
                                                  error is OverflowException)
                    {
                        Notice(error.Message);
                    }
                }
            }

            _hud.Render(_session, Objective(now), focused == null ? "" : focused.Label,
                        Time.unscaledTime < _noticeUntil ? _notice : "");
        }

        private InteractionMarker? FindNearbyStation()
        {
            InteractionMarker? nearest = null;
            float best = InteractionRadius * InteractionRadius;
            foreach (var marker in _stations)
            {
                bool available = Available(marker.Action);
                if (marker.gameObject.activeSelf != available)
                    marker.gameObject.SetActive(available);

                if (!available)
                    continue;

                float distance = (marker.transform.position - _player.transform.position)
                    .sqrMagnitude;
                if (distance < best)
                {
                    nearest = marker;
                    best = distance;
                }
            }
            return nearest;
        }

        private bool Available(StationAction action)
        {
            bool city = _session.CurrentZone == Zone.City;
            bool civilian = _session.CurrentRole == PlayerRole.Civilian;
            bool criminal = _session.CurrentRole == PlayerRole.Criminal;
            return action switch
            {
                StationAction.Scout => city && _session.Phase == HeistPhase.Idle,
                StationAction.Mask => city && civilian &&
                                      (_session.Phase == HeistPhase.Idle ||
                                       _session.Phase == HeistPhase.Scouted),
                StationAction.BeginRobbery => city && criminal &&
                                               _session.Phase == HeistPhase.Scouted,
                StationAction.Artwork => _session.Phase == HeistPhase.Robbing &&
                                         !_session.Loot.Contains("artwork-001"),
                StationAction.Watch => _session.Phase == HeistPhase.Robbing &&
                                       !_session.Loot.Contains("watch-001"),
                StationAction.Escape => _session.Phase == HeistPhase.Robbing &&
                                        _session.Loot.Count > 0,
                StationAction.Fence => _session.Phase == HeistPhase.Escaped &&
                                       _session.Loot.Count > 0,
                StationAction.CollectCash => _session.Phase == HeistPhase.CashOnCounter &&
                                            _session.CounterCash > 0,
                StationAction.Launder => _session.Phase == HeistPhase.DirtyCashCollected &&
                                         _session.DirtyCash > 0,
                StationAction.ExitCity => city && _session.Phase == HeistPhase.Laundered,
                StationAction.EnterCity => !city,
                StationAction.OpenBank => city && civilian && !_session.BankAccountOpened,
                StationAction.Deposit => city && civilian && _session.BankAccountOpened &&
                                         _session.CleanCash > 0,
                StationAction.Reset => _session.Phase == HeistPhase.Laundered &&
                                       _session.CurrentRole == PlayerRole.Civilian,
                _ => false,
            };
        }

        private void Perform(InteractionMarker marker, long now)
        {
            switch (marker.Action)
            {
                case StationAction.Scout:
                    _session.Scout();
                    break;
                case StationAction.Mask:
                    _session.PutOnMask();
                    break;
                case StationAction.BeginRobbery:
                    _session.StartHeist();
                    break;
                case StationAction.Artwork:
                    _session.TakeLoot("artwork-001");
                    break;
                case StationAction.Watch:
                    _session.TakeLoot("watch-001");
                    break;
                case StationAction.Escape:
                    _session.Escape();
                    break;
                case StationAction.Fence:
                    var quotes = new Dictionary<string, long>();
                    foreach (string item in _session.Loot)
                        quotes.Add(item, _balance.QuoteFor(item));
                    _session.SellLoot(quotes);
                    break;
                case StationAction.CollectCash:
                    _session.CollectCounterCash();
                    break;
                case StationAction.Launder:
                    long dirty = _session.DirtyCash;
                    _session.StartLaundering(dirty, _balance.CleanPayoutFor(dirty), now,
                                            _balance.LaunderingSeconds);
                    break;
                case StationAction.ExitCity:
                    _session.LeaveCity();
                    _player.WarpTo(new Vector3(0, 0.12f, -45));
                    break;
                case StationAction.EnterCity:
                    _session.EnterCity();
                    _player.WarpTo(new Vector3(0, 0.12f, -29));
                    break;
                case StationAction.OpenBank:
                    _session.OpenBankAccount();
                    break;
                case StationAction.Deposit:
                    _session.DepositCleanCash(_session.CleanCash);
                    break;
                case StationAction.Reset:
                    _session.BeginAnotherHeist();
                    break;
                default:
                    throw new ArgumentOutOfRangeException(nameof(marker.Action));
            }
        }

        private string Objective(long now)
        {
            return _session.Phase switch
            {
                HeistPhase.Idle => "Move north to the cyan SCOUT marker near the warehouse.",
                HeistPhase.Scouted when _session.CurrentRole == PlayerRole.Civilian
                    => "Activate the red MASK marker beside the warehouse.",
                HeistPhase.Scouted => "Go through the warehouse entrance to BEGIN HEIST.",
                HeistPhase.Robbing when _session.Loot.Count == 0
                    => "Find the artwork/watch pillars inside the warehouse.",
                HeistPhase.Robbing => "Take the other object or reach the green ESCAPE marker.",
                HeistPhase.Escaped => "Move to the western FENCE counter and sell your loot.",
                HeistPhase.CashOnCounter => "Pick up the physical cash pile at the counter.",
                HeistPhase.DirtyCashCollected
                    => "Take dirty cash to the eastern LAUNDERING workstation.",
                HeistPhase.Laundering => "Processing… " +
                    Math.Max(0L, _session.LaunderingReadyAt.GetValueOrDefault() - now) +
                    " seconds remaining.",
                HeistPhase.Laundered when _session.CurrentRole == PlayerRole.Criminal
                    => "Go south through the EXIT CITY marker to clear criminal status.",
                HeistPhase.Laundered when !_session.BankAccountOpened
                    => "Open a civilian bank account at the blue ATM station.",
                HeistPhase.Laundered when _session.CleanCash > 0
                    => "Deposit cleaned cash at the bank and start another heist.",
                HeistPhase.Laundered => "Visit the green NEXT HEIST marker.",
                _ => "Follow the highlighted interaction markers.",
            };
        }

        private void Notice(string message)
        {
            _notice = message;
            _noticeUntil = Time.unscaledTime + 4.5f;
        }

        private void OnDestroy()
        {
            if (_ownsBalance && _balance != null)
                Destroy(_balance);
        }
    }
}

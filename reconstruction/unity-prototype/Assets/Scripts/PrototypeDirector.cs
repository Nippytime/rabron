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
        private const float ArrestProximity = 2.5f;
        private static readonly Vector3 CustodySpawn = new Vector3(16f, 0.12f, -41f);
        private static readonly Vector3 CivilianSpawn = new Vector3(0f, 0.12f, -15f);
        private readonly RaycastHit[] _stationHits = new RaycastHit[24];
        private HeistSession _session = null!;
        private PrototypeBalance _balance = null!;
        private ThirdPersonMotor _player = null!;
        private PrototypeVehicle _vehicle = null!;
        private GuardSensor _guard = null!;
        private CashPilePresenter _cashPile = null!;
        private CourierParcelPresenter _courierParcel = null!;
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

            _session = PrototypeSaveStore.Load(out string startupMessage);
            _stations = PrototypeWorld.Create(transform, out _player, out _cashPile,
                                              out _guard);
            _courierParcel = _player.GetComponentInChildren<CourierParcelPresenter>(true);
            _vehicle = GetComponentInChildren<PrototypeVehicle>(true);

            var hudObject = new GameObject("Prototype HUD");
            hudObject.transform.SetParent(transform, false);
            _hud = hudObject.AddComponent<PrototypeHud>();
            _hud.Initialize();
            if (_session.CurrentZone == Zone.Desert)
                _player.WarpTo(new Vector3(0f, 0.12f, -45f));
            else if (_session.Phase == HeistPhase.Arrested)
                _player.WarpTo(CustodySpawn);
            _cashPile.SetAmount(_session.CounterCash);
            _courierParcel.SetCarrying(_session.CarryingCourierParcel);
            Notice(startupMessage);
        }

        private void Update()
        {
            long now = DateTimeOffset.UtcNow.ToUnixTimeSeconds();
            if (_session.Phase == HeistPhase.Laundering &&
                _session.LaunderingReadyAt <= now)
            {
                _session.CompleteLaundering(now);
                // Any failed save notice must take precedence over completion.
                Notice("Laundering complete. Leave the city to clear criminal status.");
                SaveProgress();
            }

            if (_session.Phase == HeistPhase.Robbing &&
                !_session.StaffControlled && !_session.AlarmRaised &&
                _guard.CanSee(_player.transform))
            {
                _session.RaiseAlarm();
                SaveProgress();
                Notice("ALARM RAISED! The guard spotted you. Escape with any loot.");
            }

            // A loud robbery has a real loss consequence only if the active
            // guard sees and physically reaches the player. The state change
            // and confiscation remain exclusively in the portable core.
            if (_session.Phase == HeistPhase.Robbing && _session.AlarmRaised &&
                !_session.StaffControlled &&
                (_guard.transform.position - _player.transform.position).sqrMagnitude
                    <= ArrestProximity * ArrestProximity &&
                _guard.CanSee(_player.transform))
            {
                _session.ArrestAfterAlarm();
                _player.WarpTo(CustodySpawn);
                SaveProgress();
                Notice("ARRESTED. Carried loot and dirty cash confiscated. Release at custody desk.");
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
                        SaveProgress();
                    }
                    catch (Exception error) when (error is InvalidOperationException ||
                                                  error is ArgumentException ||
                                                  error is OverflowException)
                    {
                        Notice(error.Message);
                    }
                }
            }

            // Visual only. This does not credit money or change the game state.
            _cashPile.SetAmount(_session.CounterCash);
            _courierParcel.SetCarrying(_session.CarryingCourierParcel);
            _hud.Render(_session, Objective(now),
                        _player.IsDriving ? "Exit car after stopping" :
                        focused == null ? "" : focused.Label,
                        Time.unscaledTime < _noticeUntil ? _notice : "",
                        PrototypeSaveStore.SavingDisabled,
                        PrototypeSaveStore.LastWriteFailed);
        }

        private InteractionMarker? FindNearbyStation()
        {
            if (_player.IsDriving)
            {
                foreach (var marker in _stations)
                    if (marker.gameObject.activeSelf)
                        marker.gameObject.SetActive(false);
                return null;
            }
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
                if (distance < best && CanReachStation(marker))
                {
                    nearest = marker;
                    best = distance;
                }
            }
            return nearest;
        }

        private bool CanReachStation(InteractionMarker marker)
        {
            // Don't steal through warehouse walls or reach through the counter.
            Vector3 eye = _player.transform.position + Vector3.up * 1.5f;
            return WorldOcclusion.HasClearLine(eye, marker.transform.position,
                                               _player.transform, _stationHits);
        }

        private bool Available(StationAction action)
        {
            bool city = _session.CurrentZone == Zone.City;
            bool civilian = _session.CurrentRole == PlayerRole.Civilian;
            bool criminal = _session.CurrentRole == PlayerRole.Criminal;
            return action switch
            {
                StationAction.VehicleEnter => city && civilian &&
                    _session.Phase == HeistPhase.Idle &&
                    !_session.CarryingCourierParcel && !_player.IsDriving &&
                    _vehicle != null && !_vehicle.Occupied,
                StationAction.ReleaseCustody => city &&
                    _session.Phase == HeistPhase.Arrested &&
                    _session.CurrentRole == PlayerRole.Criminal,
                StationAction.Scout => city && _session.Phase == HeistPhase.Idle &&
                                       !_session.CarryingCourierParcel,
                StationAction.CourierPickup => city && civilian &&
                    _session.Phase == HeistPhase.Idle && !_session.CarryingCourierParcel,
                StationAction.CourierDropoff => city && civilian &&
                    _session.Phase == HeistPhase.Idle && _session.CarryingCourierParcel,
                StationAction.CourierCancel => city && civilian &&
                    _session.Phase == HeistPhase.Idle && _session.CarryingCourierParcel,
                StationAction.Mask => city && civilian &&
                                      !_session.CarryingCourierParcel &&
                                      (_session.Phase == HeistPhase.Idle ||
                                       _session.Phase == HeistPhase.Scouted),
                StationAction.BeginRobbery => city && criminal &&
                                               _session.Phase == HeistPhase.Scouted,
                StationAction.Artwork => _session.Phase == HeistPhase.Robbing &&
                                         !_session.Loot.Contains("artwork-001"),
                StationAction.Watch => _session.Phase == HeistPhase.Robbing &&
                                       !_session.Loot.Contains("watch-001"),
                StationAction.ControlStaff => _session.Phase == HeistPhase.Robbing &&
                                              !_session.StaffControlled,
                StationAction.Escape => _session.Phase == HeistPhase.Robbing &&
                                        _session.Loot.Count > 0,
                StationAction.WithdrawEmptyHanded => city && criminal &&
                    _session.Phase == HeistPhase.Robbing && _session.Loot.Count == 0,
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
                case StationAction.VehicleEnter:
                    _player.BoardVehicle(_vehicle);
                    break;
                case StationAction.ReleaseCustody:
                    _session.ReleaseFromCustody();
                    _player.WarpTo(CivilianSpawn);
                    break;
                case StationAction.CourierPickup:
                    _session.PickUpCourierParcel();
                    break;
                case StationAction.CourierDropoff:
                    _session.DeliverCourierParcel(_balance.CourierReward);
                    break;
                case StationAction.CourierCancel:
                    _session.CancelCourierParcel();
                    break;
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
                case StationAction.ControlStaff:
                    _session.ControlStaff();
                    break;
                case StationAction.Escape:
                    _session.Escape();
                    break;
                case StationAction.WithdrawEmptyHanded:
                    _session.WithdrawEmptyHanded();
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
            if (_player.IsDriving)
                return "DRIVING: W/S or left stick throttle, A/D steer. Space/Y brake. Stop, then E/A to exit.";
            return _session.Phase switch
            {
                HeistPhase.Arrested
                    => "ARRESTED: belongings confiscated. Use the custody RELEASE marker to return.",
                HeistPhase.Idle when _session.CarryingCourierParcel
                    => "Deliver the parcel at the eastern kiosk, or return it to dispatch without payment.",
                HeistPhase.Idle when _session.CurrentRole == PlayerRole.Civilian
                    => "Try the parked CAR east of spawn, a legal COURIER job west, or SCOUT north.",
                HeistPhase.Idle => "Travel to the warehouse to plan your next heist.",
                HeistPhase.Scouted when _session.CurrentRole == PlayerRole.Civilian
                    => "Activate the red MASK marker beside the warehouse.",
                HeistPhase.Scouted => "Go through the warehouse entrance to BEGIN HEIST.",
                HeistPhase.Robbing when _session.AlarmRaised &&
                                         _session.Loot.Count == 0
                    => "ALARM! Evade the guard and use WITHDRAW outside to leave with no reward.",
                HeistPhase.Robbing when _session.AlarmRaised
                    => "ALARM! Finish collecting loot and escape the warehouse.",
                HeistPhase.Robbing when _session.Loot.Count == 0 && !_session.StaffControlled
                    => "Control the guard or collect loot; WITHDRAW outside for no reward.",
                HeistPhase.Robbing when _session.Loot.Count == 0
                    => "Staff controlled. Collect loot or use WITHDRAW outside for no reward.",
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

        private void SaveProgress()
        {
            if (!PrototypeSaveStore.TrySave(_session, out string error))
                Notice("Progress could not be saved: " + error);
        }

        private void OnApplicationPause(bool paused)
        {
            if (paused && _session != null)
                SaveProgress();
        }

        private void OnApplicationQuit()
        {
            if (_session != null)
                SaveProgress();
        }

        private void OnDestroy()
        {
            if (_ownsBalance && _balance != null)
                Destroy(_balance);
        }
    }
}

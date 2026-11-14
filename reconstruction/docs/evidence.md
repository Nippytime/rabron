# ROB RUN reconstruction — evidence and uncertainty ledger

Baseline examined: Nippytime/rabron main, commit 08aed4d74cf1b92316c390706c18990a65b73933 (uploaded 12 Nov 2026).
Game: ROB RUN by Kefir. The upload is a **Unity IL2CPP Windows player-data directory**, not an editable Unity project.

## Evidence tiers

- **OFFICIAL** — a behavior or fact explicitly described by Kefir (Steam/store or help center). A written rule is confirmed, but implementation details and numerical coefficients may remain unknown.
- **BUILD** — a type/class/asset name preserved in uploaded build metadata. This demonstrates that a component is referenced; it does not establish the implementation or active game balance.
- **INFERRED** — a tentative engineering hypothesis. Do not turn this into a hard-coded balance number without runtime observation.

## Official gameplay contract

| System | Confirmed behavior | Primary source |
| --- | --- | --- |
| Player roles | Masking in Looty Bay activates Criminal role; criminal status clears only by leaving the city | https://kefirgames.helpshift.com/hc/en/14-rob-run/faq/1347-how-do-i-pull-off-heists-in-looty-bay/ |
| Heists | Scout a building and getaway route; keep staff controlled to prevent an alarm; teammates can split tasks | https://kefirgames.helpshift.com/hc/en/14-rob-run/faq/1347-how-do-i-pull-off-heists-in-looty-bay/ |
| City civilian death | Bag contents and equipped gear are retained | https://kefirgames.helpshift.com/hc/en/14-rob-run/faq/1344-what-do-i-lose-when-i-die/ |
| City criminal death | Inventory is lost; surrender saves equipped gear | https://kefirgames.helpshift.com/hc/en/14-rob-run/faq/1344-what-do-i-lose-when-i-die/ |
| Police death | Department-issued gear is lost, personal items and equipment are kept (scope with respect to desert needs live verification) | https://kefirgames.helpshift.com/hc/en/14-rob-run/faq/1344-what-do-i-lose-when-i-die/ |
| Desert death | All loot is lost regardless of role; exact classification of personal gear vs loot needs observation | https://kefirgames.helpshift.com/hc/en/14-rob-run/faq/1344-what-do-i-lose-when-i-die/ |
| Surrender/bribe | Surrender forfeits bag but keeps equipped gear; accepted bribe preserves all loot | https://kefirgames.helpshift.com/hc/en/14-rob-run/faq/1352-why-surrender-to-the-cops/ |
| Fence | Sell valuables at dollar-sign van or Sales Center; cash appears physically on counter and can be taken | https://kefirgames.helpshift.com/hc/en/14-rob-run/faq/1349-how-do-i-sell-my-loot/ |
| Storage | Lenny's stores cash only; hideout stores goods but is vulnerable to raiding | https://kefirgames.helpshift.com/hc/en/14-rob-run/faq/1348-where-should-i-stash-stolen-loot/ |
| Bank | Open account as Civilian in Looty Bay; laundering at base takes time; bank funds protected from theft until wipe; withdrawals at ATM | https://kefirgames.helpshift.com/hc/en/14-rob-run/faq/1355-how-do-i-open-a-bank-account-and-why-launder-money/ |
| Income | Loot/fencing, cargo, base production, policing, and taxation by settlement/territory owners | https://kefirgames.helpshift.com/hc/en/14-rob-run/faq/1354-how-do-i-make-money/ |
| Plot ownership | Build in an owned settlement: rent vacant plot via adjacent sign; tier 2/3 district plots require documents | https://kefirgames.helpshift.com/hc/en/14-rob-run/faq/1361-how-do-i-rent-a-plot-for-my-base/ |
| Settlement taxes | Owner collects a share of tenants' spending/laundering and must physically collect it | https://kefirgames.helpshift.com/hc/en/14-rob-run/faq/1362-how-do-i-become-a-settlement-owner-and-earn-income/ |
| Wipe | Every 7 days, plots, bases, weapons, and cash reset, converting to jail time and authority; cosmetics, name, tutorial, settings and accumulated jail time persist | https://kefirgames.helpshift.com/hc/en/14-rob-run/faq/1346-what-is-the-federal-raid-wipe/ |
| Overall pitch | Human players as cops/criminals; gangs, hideouts, base raids, PvP, weekly fresh starts | https://store.steampowered.com/app/4262460/ROB_RUN/ |

### Model-to-source trace

- reconstruction/rules.py: Role transition and encounter outcomes implement the **OFFICIAL** rules above as an initial executable reference model, not reverse-compiled code.
- The all-items-lost policy for desert death is an **INFERRED interpretation** of the word “loot”; item subcategories and precedence over police-owned gear require empirical validation.
- The wipe operation requires external WipeConversion values; no original conversion coefficient has been recovered.
- Gameplay loops from public docs are a qualitative blueprint, not proof of identical runtime tuning.

## Observed evidence within this repository

The following references are from StreamingAssets/aa/AddressablesLink/link.xml (a build-time managed-type preservation/reference list). The system names are **BUILD** evidence, not recovered source methods.

| Capability | Referenced type example |
| --- | --- |
| Heists | Game.Battle.GrandHeist.GrandHeistViewDescription |
| Money laundering | Game.Battle.Entities.Plot.Dialog.MoneyLaunderingDialogView |
| Cash laundering conversion | Game.Battle.Entities.Plot.Dialog.MoneyLaunderingConversionView |
| City loot | Game.Battle.Entities.BuildingLoot.BuildingLootView |
| Prison escape | Game.Battle.Prison.Escape.PrisonEscapeView |
| Tax collection | Game.Battle.Taxes.Dialog.TaxCollectionDialogView |
| Clan war | Game.Battle.ClanBattle.ClanBattleTeamsProgressView |
| Car upgrades | Game.Battle.CarUpgrades.PoliceRadioCarUpgradeViewDescription |
| Settlement manufacturing | Game.Battle.SettlementBuilder.CargoProductionWorkbench.CargoProductionWorkbenchView |
| Safe defenses | Game.Battle.Entities.SafeDoor.SafeDoorViewDescription |
| Base defenses | Game.Battle.Entities.Plot.DefenseBlock.DefenseBlockViewDescriptions |
| Bank | Game.Battle.EntityModel.BankManager.OpenBankAccountInfoDialogView |

Other uploaded files:
- ScriptingAssemblies.json identifies client, battle, game, model, network, content, scene and rendering modules.
- RuntimeInitializeOnLoads.json contains managed initialization references.
- il2cpp_data/Metadata/global-metadata.dat is present (34,367,080 bytes in the initial tree listing). By itself it does **not** contain the full compiled method bodies.
- StreamingAssets/aa/StandaloneWindows64 contains 330 Addressables asset bundles, including 17 weapon-specific bundles, 11 car-specific bundles plus a common car bundle, locations, NPCs, UI, and a 38 MB scriptableobjects bundle (initial tree sizes).
- The repo does **not** include GameAssembly.dll or the executable; recovering complete original IL2CPP methods from this upload alone is not possible.

## Unknowns requiring extraction or controlled observation

1. Numeric payout tables: loot probabilities, heist payouts, dirty-cash conversion and time, bribe prices, bank fees, tax rates.
2. Combat: damage, reload, movement, recoil, armor, health, stamina and equipment slots.
3. Alert: alarm triggers, police dispatch, notoriety escalation and cooldowns.
4. Scene interaction: exact target positions, NPC logic, loot spawn distribution, doors and safe rules.
5. Vehicle: ownership, handling physics, fuel, acceleration, upgrades, durability and theft.
6. Base defense: building cost, decay/raid conditions, safes, fuses, decoder mechanics.
7. Cargo production: recipes, weights, yields, timers and capacity.
8. Wipe: asset-to-authority/jail-time coefficients; whether preexisting authority is accumulated or replaced.
9. Server: authoritative inventory, matchmaking, shard/instance topology, anti-cheat and persistence.
10. What assets are legally reusable in a separately distributed project. This repository's presence is not a license.

## Next extraction method

1. Keep all raw build files intact. Run the deterministic inventory command in reconstruction/README.md.
2. Inspect the Addressables catalog and scriptableobjects bundle offline using Unity-aware parsers (e.g., UnityPy / AssetRipper) in a **separate research directory**. Capture asset type, schema, GUID and numeric values with provenance.
3. For IL2CPP, pair global-metadata.dat with the matching GameAssembly.dll if acquired through an authorized copy of the local game. Validate binary/build GUID before using IL2CPP tools; metadata alone cannot prove methods.
4. Encode recovered numbers into versioned, sourced balance datasets. Unit-test formulas and replay measured sequences before using them in a playable recreation.
5. Build a fresh Unity project under reconstruction/game, using distinct assets unless appropriate licenses are confirmed.

Do not infer a formula merely from an evocative class name. Do not treat absent tests as passing.

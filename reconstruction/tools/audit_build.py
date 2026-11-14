#!/usr/bin/env python3
"""Read-only, deterministic audit of ROB RUN's checked-in Unity player data.

No executable code is run and no asset bundles are unpacked. The output records
evidence of features, not guessed balancing formulas or server behavior.
"""

import argparse
import json
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree

SYSTEM_PREFIXES = {
    "heists": ("Game.Battle.GrandHeist.", "Models.References.GrandHeist."),
    "arrest_and_prison": ("Game.Battle.Prison.", "Game.Battle.Arrest.",
                          "Game.Battle.CopSurrender", "Game.Battle.Ui.Surrender"),
    "money_laundering": ("Game.Battle.Entities.Plot.Dialog.MoneyLaundering",
                         "Game.Battle.Entities.Plot.MoneyWorkbench"),
    "housing_and_defense": ("Game.Battle.Entities.Plot.Builder.",
                            "Game.Battle.Entities.Plot.DefenseBlock.",
                            "Game.Battle.EntityModel.Plot."),
    "settlements_and_tax": ("Game.Battle.SettlementBuilder.", "Game.Battle.Taxes.",
                            "Game.Battle.EntityModel.TaxPoint."),
    "inventory_and_loot": ("Game.Battle.Inventory.",
                           "Game.Battle.Entities.BuildingLoot.",
                           "Game.Battle.EntityModel.Loot."),
    "police": ("Game.Battle.Entities.Building.PoliceBadge",
               "Game.Battle.CarUpgrades.PoliceRadio",
               "Game.Global.PoliceReinforcement"),
    "vehicles": ("Game.Battle.Car.", "Game.Battle.CarUpgrades.",
                 "Game.Battle.EntityModel.VehicleBench."),
    "clans": ("Game.Battle.ClanBattle.", "Game.Global.Clan."),
}

GAMEPLAY_ASSEMBLIES = (
    "Battle", "Game", "Models", "Global", "Realm", "Client", "Network",
    "Content", "Core", "Inputs", "Auth", "Steam", "UI", "UiState",
)


def read_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def source_files(root: Path) -> list[Path]:
    """Exclude authored research and Git internals from the raw-build inventory."""
    files = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        parts = path.relative_to(root).parts
        if parts[0] in {".git", ".github", "reconstruction"}:
            continue
        files.append(path)
    return sorted(files)


def audit(root: Path) -> dict:
    root = root.resolve()
    if not root.is_dir():
        raise ValueError("Build root must be a directory")
    assemblies = read_json(root / "ScriptingAssemblies.json")["names"]
    entrypoints = read_json(root / "RuntimeInitializeOnLoads.json")["root"]
    linker = ElementTree.parse(root / "StreamingAssets/aa/AddressablesLink/link.xml")
    types = sorted({element.attrib["fullname"] for element in linker.findall(".//type")
                    if "fullname" in element.attrib})

    files = source_files(root)
    bundle_paths = [path.relative_to(root).as_posix() for path in files
                    if path.name.endswith(".bundle")]
    bundle_groups = dict(sorted(Counter(
        Path(path).name.split("-", 1)[0].split("_", 1)[0]
        for path in bundle_paths
    ).items()))

    systems = {}
    for label, prefixes in SYSTEM_PREFIXES.items():
        names = [name for name in types if name.startswith(prefixes)]
        systems[label] = {"referenced_types": names, "count": len(names)}

    metadata_file = root / "il2cpp_data/Metadata/global-metadata.dat"
    app_file = root / "app.info"
    return {
        "evidence_only": True,
        "game": app_file.read_text(encoding="utf-8").splitlines()
        if app_file.is_file() else [],
        "raw_files": len(files),
        "raw_file_bytes_on_disk": sum(path.stat().st_size for path in files),
        "bundles": len(bundle_paths),
        "bundle_groups": bundle_groups,
        "scene_bundles": sorted(path for path in bundle_paths
                                if "_scenes_" in Path(path).name),
        "il2cpp_metadata": {
            "present": metadata_file.is_file(),
            "size_on_disk": metadata_file.stat().st_size
            if metadata_file.is_file() else None,
        },
        "game_assembly_binary_present": (root / "GameAssembly.dll").is_file(),
        "scripting_assemblies": {
            "count": len(assemblies),
            "gameplay_modules": sorted(name for name in assemblies
                                        if name.removesuffix(".dll") in GAMEPLAY_ASSEMBLIES),
        },
        "runtime_initializer_count": len(entrypoints),
        "addressables_referenced_type_count": len(types),
        "systems": systems,
        "sources": {
            "assemblies": "ScriptingAssemblies.json",
            "runtime": "RuntimeInitializeOnLoads.json",
            "types": "StreamingAssets/aa/AddressablesLink/link.xml",
            "assets": "StreamingAssets/aa/StandaloneWindows64/",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parents[2])
    parser.add_argument("--output", type=Path,
                        help="Optional JSON destination; default is stdout")
    args = parser.parse_args()
    result = json.dumps(audit(args.root), indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(result, encoding="utf-8")
    else:
        print(result, end="")


if __name__ == "__main__":
    main()

#! /usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2024 Ledger SAS

import json
import os
from pathlib import Path
import sys
from subprocess import run
from typing import Any

from pyledger.devicetree_parser import Dts, tests as dts_test

def meson_introspect(*args):
    return run(["meson", "introspect", *args], capture_output=True, check=True).stdout.strip()


def meson_package_info(build_dir: Path) -> Any:
    return json.loads(meson_introspect("--projectinfo", str(build_dir)))


def meson_scan_dependencies(build_dir: Path) -> Any:
    return json.loads(meson_introspect("--dependencies", str(build_dir)))


def task_metadata(config: dict, dts: Dts) -> dict:
    task_metadata = dict()
    capabilities = list()
    for key, value in config.items():
        if key.startswith('CONFIG_TASK_'):
            task_metadata[key[len('CONFIG_TASK_'):].lower()] = str(value).lower()

        if key.startswith('CONFIG_CAP_'):
            capabilities.append(key[len('CONFIG_CAP_'):].lower())

    task_metadata["capabilities"] = capabilities
    task_metadata["devs"] = []

    # TODO
    #  - SHMs
    #  - DMAs

    task_label = int(config["CONFIG_TASK_LABEL"], base=16)
    # Device id is DTS active node list index starting from 0
    for dev_id, dev in enumerate(dts.get_active_nodes(), start=0):
        if dts_test.is_owned_by(dev, task_label):
            task_metadata["devs"].append(dev_id)

    return task_metadata


def main(build_root: Path, source_root: Path, config: dict, dts: Dts, output: Path) -> None:
    package_info = meson_package_info(build_root)
    package_dependencies = meson_scan_dependencies(build_root)

    # standard metadata for an outpost application
    package_metadata = {
        "type": "outpost application",
        "os": "outpost",
    }

    # App name and version
    package_metadata["name"] = package_info["descriptive_name"]
    package_metadata["version"] = package_info["version"]

    # XXX
    # Use UAPI/ABI revision here

    # system dependencies (OS version and/or libshield)
    shield_found = False
    for dep in package_dependencies:
        if ("name", "shield") in dep.items() and len(dep["version"]) > 0:
            package_metadata["libshield_version"] = dep["version"]
            shield_found = True

    # if not found w/ pkgconfig, search internal deps in meson package_info
    for dep in package_info["subprojects"]:
        if ("name", "libshield") in dep.items():
            package_metadata["libshield_version"] = dep["version"]
            shield_found = True

    assert shield_found, "libshield dependency not found"

    package_metadata["task"] = task_metadata(config, dts)

    with output.open("w") as out:
        out.write("--package-metadata='")
        json.dump(package_metadata, out)
        out.write("'")


if __name__ == "__main__":
    from argparse import ArgumentParser

    parser = ArgumentParser(prog="gen-package-metadata", add_help=True)
    parser.add_argument("output", type=Path, action="store")
    parser.add_argument("--build-root", type=Path, action="store", help="top level project build root directory")
    parser.add_argument("--source-root", type=Path, action="store", help="top level project source root directory")
    parser.add_argument("--config", type=Path, action="store", help="configuration file (from KConfig) in json")
    parser.add_argument("--dts", type=Path, action="store", help="dts file")
    args = parser.parse_args()

    assert args.build_root.resolve(strict=True).is_dir()
    assert args.source_root.resolve(strict=True).is_dir()
    assert args.config.resolve(strict=True).exists()
    assert args.dts.resolve(strict=True).exists()

    with args.config.open("r") as config:
        main(
            build_root=args.build_root,
            source_root=args.source_root,
            config=json.load(config),
            dts=Dts(args.dts),
            output=args.output,
        )

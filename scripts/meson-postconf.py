#! /usr/bin/env python3

# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2023 Ledger SAS

import json
import os
from subprocess import run


PACKAGE_SOURCE_DIR = os.getenv("MESON_SOURCE_ROOT")
PACKAGE_BUILD_DIR = os.getenv("MESON_BUILD_ROOT")


def meson_introspect(*args):
	return run(["meson", "introspect", *args], capture_output=True, check=True).stdout.strip()


def meson_package_info():
	return json.loads(meson_introspect("--projectinfo", PACKAGE_BUILD_DIR))


def meson_scan_dependencies():
	return json.loads(meson_introspect("--scan-dependencies", os.path.join(PACKAGE_SOURCE_DIR, "meson.build")))


package_info = meson_package_info()
package_dependencies = meson_scan_dependencies()

# standard metadata for an outpost application
package_metadata = {
	"type": "outpost application",
	"os": "outpost",
}

# App name and version
package_metadata["name"] = package_info["descriptive_name"]
package_metadata["version"] = package_info["version"]

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

with open(os.path.join(PACKAGE_BUILD_DIR, "package-metadata.json"), "w") as out:
	out.write("--package-metadata='")
	json.dump(package_metadata, out)
	out.write("'")

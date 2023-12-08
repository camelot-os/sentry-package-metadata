# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2023 Ledger SAS

project(
    'package-metadata',
    'c',
    meson_version: '>=1.3.0',
    license: 'Apache-2.0',
    license_files: [ 'LICENSE' ],
    version: run_command('dunamai', 'from', 'git', '--style', 'semver', '--dirty', check: true).stdout().strip(),
)

package_metadata_postconfig = find_program('scripts/meson-postconf.py')
meson.add_postconf_script(package_metadata_postconfig)

package_metadata_dep = declare_dependency(
    link_args: ['-Xlinker', '--build-id', '-Xlinker', '@package-metadata.json']
)

# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2023-2024 Ledger SAS

project(
    'package-metadata',
    'c',
    meson_version: '>=1.3.0',
    license: 'Apache-2.0',
    license_files: [ 'LICENSE' ],
    version: run_command('dunamai', 'from', 'git', '--style', 'semver', '--dirty', check: true).stdout().strip(),
)

# XXX
# This meson project is a helper project that aims to be used as subproject only
if not meson.is_subproject()
error('Use this as subproject only')
endif

# Note that this will fail if top level project does not use Kconfig nor DTS
# Use meson recipe only for meson top level package
# For other buildsystem, use the correct recipe (TBD).
if get_option('with_task_metadata')
kconfig_proj = subproject('kconfig')
kconfig_json = kconfig_proj.get_variable('kconfig_json')
devicetree_proj = subproject('devicetree')
dts = devicetree_proj.get_variable('devicetree_dtsd')

gen_package_metadata = find_program('scripts/gen-package-metadata.py')

package_metadata = custom_target(
    input: [kconfig_json, dts],
    output: 'package-metadata.json',
    command: [
        gen_package_metadata,
        '--build-root=@BUILD_ROOT@',
        '--source-root=@SOURCE_ROOT@',
        '--config=@INPUT0@',
        '--dts=@INPUT1@',
        '@OUTPUT@'
    ],
)

package_metadata_link_args = ['-Xlinker', '@' + package_metadata.full_path()]
endif

if get_option('with_build_id')
    package_metadata_link_args += ['-Xlinker', '--build-id' ]
endif

package_metadata_dep = declare_dependency(
    link_args: package_metadata_link_args,
    sources: package_metadata,
)

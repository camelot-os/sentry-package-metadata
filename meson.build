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

# XXX
# This meson project is a helper project that aims to be used as subproject only
if not meson.is_subproject()
error('Use this as subproject only')
endif

package_metadata_link_args = ['-Xlinker', '@package-metadata.json']
package_metadata_postconf_script_args = []

# Note that this will fail if top level project does not use Kconfig
# The lack of top level kconfig is mandatory otherwise, but, as long as this is
# pointless to use this project as top level project, wa can use kconfig subproject
# without defining our own Kconfig
if get_option('with_task_metadata')
kconfig_proj = subproject('kconfig')
kconfig_dotconfig = kconfig_proj.get_variable('kconfig_dotconfig')
# We made direct usage of dotconfig here as this script is ran in postconf,
# thus, the config file exists and it is up to date
package_metadata_postconf_script_args += kconfig_dotconfig
endif

if get_option('with_build_id')
    package_metadata_link_args += ['-Xlinker', '--build-id' ]
endif

package_metadata_postconfig = find_program('scripts/meson-postconf.py')
meson.add_postconf_script(package_metadata_postconfig, package_metadata_postconf_script_args)

package_metadata_dep = declare_dependency(
    link_args: package_metadata_link_args,
)

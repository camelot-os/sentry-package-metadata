# meson-app-metadata

Append outpost metadata to an application at link time using the [Elf Package Metadata](https://systemd.io/ELF_PACKAGE_METADATA/) standard

## Pre requisites
 - Python 3.10+
 - The Meson Build System (>= 1.3.0)
 - Dunamai

## How To

While used as [meson subproject](https://mesonbuild.com/Subprojects.html) this package automatically adds a custom target that use project [introspection](https://mesonbuild.com/Commands.html#introspect) and Kconfig json output and preprocessed dts in order to generates outpost application relative metadata in a text file to be used as linker option.

In order to add the `.note.*` section(s) to the generated elf file, one must add the meson internal dependency to the dependencies list of its executable.

### Usage example

```python
project('outpost-app', [...])

[...]

app_metadata_proj = subproject('meson-app-metadata')
app_metadata_dep = app_metadata_proj.get_variable('package_metadata_dep')
outpost_app_deps += [ app_metadata_dep ]


executable(meson.project_name(),
    [...]
    dependencies: [ outpost_app_deps ],
    [...]
)
```

## Metadata

ELF package metadata is a JSon file with the following entry in the case of an outpost application.

### generic metadata
The following metadata are fetched from `meson introspect` command, those are string typed.
 - `type`: `outpost application`
 - `os`: `outpost`
 - `name`: Application Name, based on the meson project name
 - `version`: Application version, based on the meson project version
 - `libshield_version`: Version of the C runtime used (a.k.a. libshield)
 Task configuration is a json node filled with Task config in the task `.config` used (see https://git.orange.ledgerlabs.net/outpost/sentry-kernel/blob/main/uapi/task.Kconfig)
 - `task`: outpost task configuration (json object)

### task configuration metadata
 - `priority`: task priority
 - `quantum`: task jiffies quantum allowed
 - `auto_start`: task start policy (auto or manually)
 - `exit_policy`: policy on task exit (panic, restart, norestart)
 - `stack_size`: task stack size in Bytes
 - `heap_size`: task heap size in Bytes (it is up to the task to implements its own allocator)
 - `capabilities`: Array of outpost system capabilities
 - `devs`: Array of owned device ids

 ### Example
 Here an example of metadata added to the `.note.package` ELF section.

 ```console
 $ /opt/arm-none-eabi/bin/arm-none-eabi-readelf --notes app-sample.elf

Displaying notes found in: .note.package
  Owner                Data size        Description
  FDO                  0x000001f4       FDO_PACKAGING_METADATA
    Packaging Metadata: {"type": "outpost application", "os": "outpost", "name": "app-sample", "version": "0.0.0-post.14+c6ed142.dirty", "libshield_version": "0.0.0-post.8+ccf3a11.dirty", "task": {"priority": "42", "quantum": "4", "auto_start": "true", "exit_norestart": "true", "stack_size": "0x200", "heap_size": "0x400", "magic_value": "0xdeadcafe", "capabilities": ["dev_buses", "dev_io", "dev_timer", "dev_storage", "dev_crypto", "dev_power", "sys_power", "sys_procstart", "mem_shm_own", "mem_shm_use", "cry_krng"], "devs": [0, 1]}}
 ```

## License
Licensed under Apache-2.0

> see [LICENSE](LICENSE) file

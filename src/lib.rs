// SPDX-License-Identifier: Apache-2.0
//
// SPDX-FileCopyrightText: 2024 Ledger SAS

use std::env;
use std::io::Write;
use std::path::Path;

use cargo_metadata;
use serde_json::{json, Value};

use kconfig_import;
// TODO: use devicetree

// XXX ? Victor did this
#[derive(Debug)]
pub enum Error {
    IOError,
}

impl From<std::io::Error> for Error {
    fn from(_: std::io::Error) -> Error {
        Error::IOError
    }
}

pub fn cargo_package_introspect(manifest: Option<&str>) -> cargo_metadata::Metadata {
    let mut cmd = cargo_metadata::MetadataCommand::new();

    match manifest {
        Some(path) => cmd.manifest_path(path),
        None => &mut cmd,
    };

    cmd.exec().expect("Could not execute `cargo metadata`")
}

fn get_version(name: &str, introspect: &cargo_metadata::Metadata) -> Option<String> {
    let package = introspect.packages.iter().find(|&p| p.name == name)?;
    Some(package.version.to_string())
}

fn task_metadata(config: Option<&str>, _dts: Option<&str>) -> Value {
    let dotconfig_filename = &config.unwrap_or(".config");
    let data = std::fs::read_to_string(dotconfig_filename).unwrap();
    let dotconfig = kconfig_import::DotConfig::from(data.as_str());

    let mut metadata = json!({});
    let mut capabilities = json!([]);

    for (key, value) in dotconfig.into_iter() {
        if let Some(k) = key.strip_prefix("CONFIG_TASK_") {
            // For legacy reason (old kconfig backend w/ 1/0 boolean)
            // convert entry to "y" to "1".
            // TODO: change to boolean here and in python code.
            metadata[k.to_lowercase()] = match value {
                "y" => json!("1"),
                _ => json!(value),
            };
        } else if let Some(k) = key.strip_prefix("CONFIG_CAP_") {
            // XXX:
            //  can't add item in array with index_mut (i.e. capabilities[I])
            //  so we have to borrow mutable ref to array (underlying type is Vec<Value>).
            capabilities.as_array_mut().unwrap().push(json!(k.to_lowercase()));
        }
    }

    metadata["capabilities"] = capabilities;

    // Todo:
    // metadata["devs"] = json!([]);
    // metadata["shms"] = json!([]);
    // metadata["dmas"] = json!([]);

    metadata
}

pub fn gen_package_metadata(
    name: &str,
    introspect: cargo_metadata::Metadata,
    config: Option<&str>,
    _dts: Option<&str>,
) -> Result<(), Error> {
    let mut package_metadata = json!({"type": "outpost application", "os": "outpost"});
    let version = get_version(name, &introspect).unwrap();
    let uapi_version = get_version("uapi", &introspect);
    let shield_version = get_version("shield", &introspect);
    let out_var = &env::var("OUT_DIR").unwrap();
    let out_dir = Path::new(&out_var);
    let metadata_filepath = out_dir.join("package_metadata.json");

    package_metadata["name"] = json!(name);
    package_metadata["version"] = json!(version);

    match uapi_version {
        Some(v) => package_metadata["uapi_version"] = json!(v),
        None => println!("cargo::warning=uapi dependency not found"),
    };

    match shield_version {
        Some(v) => package_metadata["libshield_version"] = json!(v),
        None => println!("cargo::warning=shield dependency not found"),
    };

    package_metadata["task"] = task_metadata(config, _dts);

    let mut metadata_file = std::fs::File::create(&metadata_filepath)?;
    let metadata_str = format!("--package-metadata='{}'", package_metadata.to_string());
    metadata_file.write_all(metadata_str.as_bytes())?;

    // XXX:
    //  According to the given linker in use, exported link arg is slightly different
    //  with gcc as linker, gcc will wrapped ld calls, some options are gcc ones,
    //  linker options are prefixed by `-Wl,` or `-Xlinker`
    let metadata_link_arg = match std::env::var("RUSTC_LINKER") {
        Ok(linker) if linker.ends_with("gcc") => format!("-Wl,@{}", metadata_filepath.display()),
        _ => format!("@{}", metadata_filepath.display()),
    };

    println!("cargo::rustc-link-arg-bins={}", metadata_link_arg);

    Ok(())
}

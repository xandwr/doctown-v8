use std::path::Path;
use std::process::Command;
use std::fs;
use std::io;

pub fn run(docpack: &str, image: &str, follow: bool, env_file: Option<&str>) -> Result<(), Box<dyn std::error::Error>> {
    let docpack_path = Path::new(docpack);

    // Validate docpack exists
    if !docpack_path.exists() {
        return Err(format!("Docpack does not exist: {}", docpack).into());
    }

    // Check if this is a zip file that needs extraction
    let working_dir = if docpack_path.is_file() && docpack.ends_with(".docpack") {
        println!("Extracting .docpack archive...");

        // Create a temporary directory for extraction
        let temp_dir = std::env::temp_dir().join(format!("docpack-run-{}", std::process::id()));
        fs::create_dir_all(&temp_dir)?;

        // Extract the zip file
        extract_zip(docpack_path, &temp_dir)?;

        println!("  Extracted to: {}", temp_dir.display());
        temp_dir
    } else if docpack_path.is_dir() {
        // It's already a directory
        if !docpack_path.join("docpack.json").exists() {
            return Err(format!("Not a valid .docpack (missing docpack.json): {}", docpack).into());
        }
        docpack_path.to_path_buf()
    } else {
        return Err(format!("Invalid .docpack: must be either a .docpack zip file or a directory containing docpack.json").into());
    };

    println!("Running documenter on: {}", working_dir.display());
    println!("Using Docker image: {}", image);
    println!();

    // Get absolute path for Docker mount
    let abs_path = std::fs::canonicalize(&working_dir)?;

    // Build docker run command
    let mut cmd = Command::new("docker");
    cmd.arg("run")
        .arg("--rm");
    
    // Add --env-file if provided or if .env exists in current dir
    if let Some(env_path) = env_file {
        if Path::new(env_path).exists() {
            cmd.arg("--env-file").arg(env_path);
        }
    } else if Path::new(".env").exists() {
        cmd.arg("--env-file").arg(".env");
    }
    
    cmd.arg("-v")
        .arg(format!("{}:/workspace", abs_path.display()))
        .arg(image);

    if follow {
        println!("Following logs...\n");
        println!("{}", "=".repeat(60));
    }

    // Execute docker run
    let status = cmd.status()?;

    if !status.success() {
        return Err(format!("Docker command failed with exit code: {:?}", status.code()).into());
    }

    println!("\n{}", "=".repeat(60));
    println!("✓ Documenter completed successfully");
    println!("\nOutput files written to: {}/output/", working_dir.display());

    // List output files
    let output_dir = working_dir.join("output");
    if output_dir.exists() {
        println!("\nGenerated files:");
        for entry in std::fs::read_dir(output_dir)? {
            let entry = entry?;
            if entry.file_type()?.is_file() {
                let metadata = entry.metadata()?;
                println!("  - {} ({} bytes)",
                    entry.file_name().to_string_lossy(),
                    metadata.len()
                );
            }
        }
    }

    // Clean up temporary directory if we extracted a zip
    if docpack_path.is_file() && working_dir != docpack_path {
        println!("\nNote: Extracted files are in temporary directory: {}", working_dir.display());
        println!("They will be cleaned up on next system restart.");
    }

    Ok(())
}

fn extract_zip(zip_path: &Path, extract_to: &Path) -> Result<(), Box<dyn std::error::Error>> {
    let file = fs::File::open(zip_path)?;
    let mut archive = zip::ZipArchive::new(file)?;

    for i in 0..archive.len() {
        let mut file = archive.by_index(i)?;
        let outpath = match file.enclosed_name() {
            Some(path) => extract_to.join(path),
            None => continue,
        };

        if file.name().ends_with('/') {
            fs::create_dir_all(&outpath)?;
        } else {
            if let Some(p) = outpath.parent() {
                if !p.exists() {
                    fs::create_dir_all(p)?;
                }
            }
            let mut outfile = fs::File::create(&outpath)?;
            io::copy(&mut file, &mut outfile)?;
        }

        // Set permissions on Unix
        #[cfg(unix)]
        {
            use std::os::unix::fs::PermissionsExt;
            if let Some(mode) = file.unix_mode() {
                fs::set_permissions(&outpath, fs::Permissions::from_mode(mode))?;
            }
        }
    }

    Ok(())
}

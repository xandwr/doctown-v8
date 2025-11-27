use std::path::Path;
use std::process::Command;

pub fn run(docpack: &str, image: &str, follow: bool) -> Result<(), Box<dyn std::error::Error>> {
    let docpack_path = Path::new(docpack);

    // Validate docpack exists
    if !docpack_path.exists() {
        return Err(format!("Docpack does not exist: {}", docpack).into());
    }

    if !docpack_path.join("docpack.json").exists() {
        return Err(format!("Not a valid .docpack (missing docpack.json): {}", docpack).into());
    }

    println!("Running documenter on: {}", docpack);
    println!("Using Docker image: {}", image);
    println!();

    // Get absolute path for Docker mount
    let abs_path = std::fs::canonicalize(docpack_path)?;

    // Build docker run command
    let mut cmd = Command::new("docker");
    cmd.arg("run")
        .arg("--rm")
        .arg("--env-file")
        .arg(".env")
        .arg("-v")
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
    println!("\nOutput files written to: {}/output/", docpack);

    // List output files
    let output_dir = docpack_path.join("output");
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

    Ok(())
}

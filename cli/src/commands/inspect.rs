use std::fs;
use std::path::Path;
use serde_json::Value;

pub fn run(docpack: &str, verbose: bool) -> Result<(), Box<dyn std::error::Error>> {
    let docpack_path = Path::new(docpack);

    // Validate docpack exists
    if !docpack_path.exists() {
        return Err(format!("Docpack does not exist: {}", docpack).into());
    }

    println!("Inspecting .docpack: {}\n", docpack);

    // Read and parse manifest
    let manifest_path = docpack_path.join("docpack.json");
    if !manifest_path.exists() {
        return Err("Not a valid .docpack (missing docpack.json)".into());
    }

    let manifest_content = fs::read_to_string(&manifest_path)?;
    let manifest: Value = serde_json::from_str(&manifest_content)?;

    // Display basic info
    println!("📦 Docpack Information");
    println!("{}", "─".repeat(60));
    println!("Name:        {}", manifest["name"].as_str().unwrap_or("unknown"));
    println!("Version:     {}", manifest["version"].as_str().unwrap_or("unknown"));
    println!("Description: {}", manifest["description"].as_str().unwrap_or("none"));
    println!();

    // Display metadata if present
    if let Some(metadata) = manifest["metadata"].as_object() {
        println!("📋 Metadata");
        println!("{}", "─".repeat(60));
        if let Some(created) = metadata.get("created").and_then(|v| v.as_str()) {
            println!("Created:     {}", created);
        }
        if let Some(creator) = metadata.get("creator").and_then(|v| v.as_str()) {
            println!("Creator:     {}", creator);
        }
        if let Some(source_type) = metadata.get("source_type").and_then(|v| v.as_str()) {
            println!("Source Type: {}", source_type);
        }
        if let Some(language) = metadata.get("language").and_then(|v| v.as_str()) {
            println!("Language:    {}", language);
        }
        println!();
    }

    // Display environment settings
    if let Some(env) = manifest["environment"].as_object() {
        println!("🔧 Environment");
        println!("{}", "─".repeat(60));

        if let Some(tools) = env.get("tools").and_then(|v| v.as_array()) {
            println!("Tools enabled: {}", tools.len());
            if verbose {
                for tool in tools {
                    println!("  - {}", tool.as_str().unwrap_or("unknown"));
                }
            }
        }

        if let Some(constraints) = env.get("constraints").and_then(|v| v.as_object()) {
            if verbose {
                println!("\nConstraints:");
                for (key, value) in constraints {
                    println!("  {}: {}", key, value);
                }
            }
        }
        println!();
    }

    // Display file statistics
    println!("📁 Content");
    println!("{}", "─".repeat(60));
    let files_dir = docpack_path.join("files");
    if files_dir.exists() {
        let file_count = count_files(&files_dir)?;
        let total_size = dir_size(&files_dir)?;
        println!("Files:       {} files", file_count);
        println!("Total size:  {} bytes ({:.2} MB)", total_size, total_size as f64 / 1_048_576.0);

        if verbose {
            println!("\nFile tree:");
            print_tree(&files_dir, &files_dir, "", true)?;
        }
    } else {
        println!("Files:       (no files directory)");
    }
    println!();

    // Display index information
    println!("🔍 Index");
    println!("{}", "─".repeat(60));
    let index_dir = docpack_path.join("index");
    if index_dir.exists() {
        let has_search = index_dir.join("search.json").exists();
        let has_graph = index_dir.join("graph.json").exists();
        let has_embeddings = index_dir.join("embeddings.bin").exists();

        println!("Search index:   {}", if has_search { "✓" } else { "✗" });
        println!("Semantic graph: {}", if has_graph { "✓" } else { "✗" });
        println!("Embeddings:     {}", if has_embeddings { "✓" } else { "✗" });
    } else {
        println!("(no index directory)");
    }
    println!();

    // Display tasks if present
    let tasks_path = docpack_path.join("tasks.json");
    if tasks_path.exists() {
        let tasks_content = fs::read_to_string(&tasks_path)?;
        let tasks: Value = serde_json::from_str(&tasks_content)?;

        println!("🎯 Tasks");
        println!("{}", "─".repeat(60));
        if let Some(mission) = tasks["mission"].as_str() {
            println!("Mission: {}", mission);
        }

        if let Some(task_list) = tasks["tasks"].as_array() {
            println!("Tasks:   {} defined", task_list.len());
            if verbose {
                println!();
                for (i, task) in task_list.iter().enumerate() {
                    println!("  {}. {}", i + 1, task["name"].as_str().unwrap_or("unnamed"));
                    if let Some(desc) = task["description"].as_str() {
                        println!("     {}", desc);
                    }
                }
            }
        }
        println!();
    }

    // Display output information
    let output_dir = docpack_path.join("output");
    if output_dir.exists() {
        let output_count = count_files(&output_dir)?;
        if output_count > 0 {
            println!("📤 Output");
            println!("{}", "─".repeat(60));
            println!("Generated files: {}", output_count);

            if verbose {
                for entry in fs::read_dir(&output_dir)? {
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
            println!();
        }
    }

    Ok(())
}

fn count_files(dir: &Path) -> std::io::Result<usize> {
    let mut count = 0;
    if dir.is_dir() {
        for entry in fs::read_dir(dir)? {
            let entry = entry?;
            if entry.file_type()?.is_dir() {
                count += count_files(&entry.path())?;
            } else {
                count += 1;
            }
        }
    }
    Ok(count)
}

fn dir_size(dir: &Path) -> std::io::Result<u64> {
    let mut size = 0;
    if dir.is_dir() {
        for entry in fs::read_dir(dir)? {
            let entry = entry?;
            let path = entry.path();
            if path.is_dir() {
                size += dir_size(&path)?;
            } else {
                size += entry.metadata()?.len();
            }
        }
    }
    Ok(size)
}

fn print_tree(path: &Path, base: &Path, prefix: &str, _is_last: bool) -> std::io::Result<()> {
    let entries: Vec<_> = fs::read_dir(path)?
        .filter_map(|e| e.ok())
        .collect();

    for (i, entry) in entries.iter().enumerate() {
        let is_last_entry = i == entries.len() - 1;
        let name = entry.file_name();
        let name_str = name.to_string_lossy();

        let connector = if is_last_entry { "└── " } else { "├── " };
        println!("{}{}{}", prefix, connector, name_str);

        if entry.file_type()?.is_dir() {
            let new_prefix = format!(
                "{}{}",
                prefix,
                if is_last_entry { "    " } else { "│   " }
            );
            print_tree(&entry.path(), base, &new_prefix, is_last_entry)?;
        }
    }

    Ok(())
}

use std::fs;
use std::path::Path;
use std::io::{self, Write};
use serde_json::json;
use zip::write::FileOptions;
use zip::ZipWriter;
use zip::CompressionMethod;

pub fn run(
    source: &str,
    out: &str,
    name: Option<&str>,
    description: Option<&str>,
    language: Option<&str>,
    all_tools: bool,
    build_index: bool,
    build_graph: bool,
) -> Result<(), Box<dyn std::error::Error>> {
    println!("Creating .docpack from source: {}", source);

    let source_path = Path::new(source);

    // Validate source exists
    if !source_path.exists() {
        return Err(format!("Source path does not exist: {}", source).into());
    }

    // Determine docpack name
    let docpack_name = name.unwrap_or_else(|| {
        source_path
            .file_name()
            .and_then(|n| n.to_str())
            .unwrap_or("untitled")
    });

    // Create a temporary directory for building the docpack
    let temp_dir = std::env::temp_dir().join(format!("docpack-build-{}", std::process::id()));
    fs::create_dir_all(&temp_dir)?;

    // Create .docpack directory structure in temp
    println!("Creating directory structure...");
    fs::create_dir_all(temp_dir.join("files"))?;
    fs::create_dir_all(temp_dir.join("index"))?;
    fs::create_dir_all(temp_dir.join("output"))?;

    // Copy source files to files/
    println!("Copying source files...");
    copy_dir_all(source_path, &temp_dir.join("files"))?;

    // Count files for reporting
    let file_count = count_files(&temp_dir.join("files"))?;
    println!("  Copied {} files", file_count);

    // Create docpack.json manifest
    println!("Creating manifest...");
    let tools = if all_tools {
        vec![
            "list_files",
            "read_file",
            "read_image",
            "read_pdf",
            "search_code",
            "semantic_search",
            "query_graph",
            "write_output",
        ]
    } else {
        vec!["list_files", "read_file", "write_output"]
    };

    let manifest = json!({
        "version": "1.0",
        "name": docpack_name,
        "description": description.unwrap_or("Generated docpack"),
        "environment": {
            "tools": tools,
            "interpreter": "python3.12",
            "constraints": {
                "max_file_reads": 1000,
                "max_execution_time_seconds": 300,
                "memory_limit_mb": 2048
            }
        },
        "metadata": {
            "created": chrono::Utc::now().to_rfc3339(),
            "creator": "localdoc-cli",
            "source_type": "directory",
            "language": language.unwrap_or("unknown")
        }
    });

    let manifest_path = temp_dir.join("docpack.json");
    let mut manifest_file = fs::File::create(&manifest_path)?;
    manifest_file.write_all(serde_json::to_string_pretty(&manifest)?.as_bytes())?;
    println!("  Created docpack.json");

    // Create minimal tasks.json
    println!("Creating tasks.json...");
    let tasks = json!({
        "mission": "Explore and document this project",
        "tasks": [
            {
                "id": "task_1",
                "name": "Analyze project structure",
                "description": "Explore the codebase and create a high-level overview",
                "tools_allowed": tools,
                "output": {
                    "type": "markdown",
                    "path": "output/overview.md"
                }
            }
        ],
        "constraints": {
            "chain_of_thought_location": "/workspace/.reasoning",
            "forbidden_actions": ["modify_files", "execute_code"],
            "output_format": "markdown"
        }
    });

    let tasks_path = temp_dir.join("tasks.json");
    let mut tasks_file = fs::File::create(&tasks_path)?;
    tasks_file.write_all(serde_json::to_string_pretty(&tasks)?.as_bytes())?;
    println!("  Created tasks.json");

    // Build index if requested
    if build_index {
        println!("Building search index...");
        build_search_index(&temp_dir.join("files"), &temp_dir.join("index"))?;
        println!("  Created index/search.json");
    }

    // Build graph if requested
    if build_graph {
        println!("Building semantic graph...");
        println!("  Note: Full graph building requires code analysis (coming soon)");
        create_empty_graph(&temp_dir.join("index"))?;
        println!("  Created index/graph.json (empty template)");
    }

    // Create the zip archive
    println!("Creating zip archive...");
    let out_path = Path::new(out);

    // Ensure output path has .docpack extension
    let zip_path = if out.ends_with(".docpack") {
        out_path.to_path_buf()
    } else {
        out_path.with_extension("docpack")
    };

    create_zip_archive(&temp_dir, &zip_path)?;

    // Clean up temp directory
    fs::remove_dir_all(&temp_dir)?;

    println!("\n✓ Successfully created .docpack archive: {}", zip_path.display());
    println!("\nNext steps:");
    println!("  1. Run: localdoc run {}", zip_path.display());
    println!("  2. The archive will be automatically extracted and processed");

    Ok(())
}

fn copy_dir_all(src: &Path, dst: &Path) -> io::Result<()> {
    if src.is_dir() {
        for entry in fs::read_dir(src)? {
            let entry = entry?;
            let ty = entry.file_type()?;
            let dst_path = dst.join(entry.file_name());

            if ty.is_dir() {
                fs::create_dir_all(&dst_path)?;
                copy_dir_all(&entry.path(), &dst_path)?;
            } else {
                fs::copy(entry.path(), dst_path)?;
            }
        }
    } else {
        // Source is a single file
        fs::copy(src, dst)?;
    }
    Ok(())
}

fn count_files(dir: &Path) -> io::Result<usize> {
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

fn build_search_index(files_dir: &Path, index_dir: &Path) -> Result<(), Box<dyn std::error::Error>> {
    use std::collections::HashMap;

    let mut index: HashMap<String, Vec<String>> = HashMap::new();

    // Simple word-based indexing
    for entry in walkdir::WalkDir::new(files_dir) {
        let entry = entry?;
        if entry.file_type().is_file() {
            let path = entry.path();

            // Only index text files
            if let Ok(content) = fs::read_to_string(path) {
                let rel_path = path.strip_prefix(files_dir)?;

                // Extract words and add to index
                for word in content.split_whitespace() {
                    let word_clean = word.to_lowercase()
                        .trim_matches(|c: char| !c.is_alphanumeric())
                        .to_string();

                    if word_clean.len() > 2 {
                        index.entry(word_clean)
                            .or_insert_with(Vec::new)
                            .push(format!("{}:1", rel_path.display()));
                    }
                }
            }
        }
    }

    // Deduplicate entries
    for entries in index.values_mut() {
        entries.sort();
        entries.dedup();
    }

    let search_index = json!({
        "index": index,
        "metadata": {
            "total_files": count_files(files_dir)?,
            "indexed_at": chrono::Utc::now().to_rfc3339()
        }
    });

    let search_path = index_dir.join("search.json");
    let mut search_file = fs::File::create(&search_path)?;
    search_file.write_all(serde_json::to_string_pretty(&search_index)?.as_bytes())?;

    Ok(())
}

fn create_empty_graph(index_dir: &Path) -> Result<(), Box<dyn std::error::Error>> {
    let graph = json!({
        "nodes": [],
        "edges": [],
        "metadata": {
            "created": chrono::Utc::now().to_rfc3339(),
            "note": "Empty graph template - populate with code analysis"
        }
    });

    let graph_path = index_dir.join("graph.json");
    let mut graph_file = fs::File::create(&graph_path)?;
    graph_file.write_all(serde_json::to_string_pretty(&graph)?.as_bytes())?;

    Ok(())
}

fn create_zip_archive(source_dir: &Path, zip_path: &Path) -> Result<(), Box<dyn std::error::Error>> {
    let file = fs::File::create(zip_path)?;
    let mut zip = ZipWriter::new(file);
    let options = FileOptions::default()
        .compression_method(CompressionMethod::Deflated)
        .unix_permissions(0o644);

    // Configure walkdir to not follow symlinks
    let walkdir = walkdir::WalkDir::new(source_dir)
        .follow_links(false);

    for entry in walkdir {
        let entry = entry?;
        let path = entry.path();

        // Skip symlinks entirely
        if path.is_symlink() {
            continue;
        }

        let name = path.strip_prefix(source_dir)?;

        // Skip the root directory itself
        if name.as_os_str().is_empty() {
            continue;
        }

        // Convert path to string for zip entry name
        let name_str = name.to_str().ok_or("Invalid UTF-8 in path")?.to_string();

        if path.is_file() {
            // Add file
            zip.start_file(&name_str, options)?;
            let mut f = fs::File::open(path)
                .map_err(|e| format!("Failed to open file {:?}: {}", path, e))?;
            io::copy(&mut f, &mut zip)
                .map_err(|e| format!("Failed to copy file {:?}: {}", path, e))?;
        } else if path.is_dir() {
            // Add directory
            let dir_name = if name_str.ends_with('/') {
                name_str
            } else {
                format!("{}/", name_str)
            };
            zip.add_directory(&dir_name, options)?;
        }
    }

    zip.finish()?;
    Ok(())
}

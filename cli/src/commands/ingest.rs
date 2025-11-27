use std::fs;
use std::path::Path;
use std::io::{self, Write};
use serde_json::json;

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

    let out_path = Path::new(out);

    // Create .docpack directory structure
    println!("Creating directory structure at: {}", out);
    fs::create_dir_all(out_path)?;
    fs::create_dir_all(out_path.join("files"))?;
    fs::create_dir_all(out_path.join("index"))?;
    fs::create_dir_all(out_path.join("output"))?;

    // Copy source files to files/
    println!("Copying source files...");
    copy_dir_all(source_path, &out_path.join("files"))?;

    // Count files for reporting
    let file_count = count_files(&out_path.join("files"))?;
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

    let manifest_path = out_path.join("docpack.json");
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

    let tasks_path = out_path.join("tasks.json");
    let mut tasks_file = fs::File::create(&tasks_path)?;
    tasks_file.write_all(serde_json::to_string_pretty(&tasks)?.as_bytes())?;
    println!("  Created tasks.json");

    // Build index if requested
    if build_index {
        println!("Building search index...");
        build_search_index(&out_path.join("files"), &out_path.join("index"))?;
        println!("  Created index/search.json");
    }

    // Build graph if requested
    if build_graph {
        println!("Building semantic graph...");
        println!("  Note: Full graph building requires code analysis (coming soon)");
        create_empty_graph(&out_path.join("index"))?;
        println!("  Created index/graph.json (empty template)");
    }

    println!("\n✓ Successfully created .docpack: {}", out);
    println!("\nNext steps:");
    println!("  1. Review {}/tasks.json and customize your documentation goals", out);
    println!("  2. Run: localdoc run {}", out);
    println!("  3. Check output in {}/output/", out);

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

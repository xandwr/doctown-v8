use std::fs;
use std::path::Path;
use std::io::Write;
use serde_json::json;

pub fn run(path: &str, name: Option<&str>, with_tasks: bool) -> Result<(), Box<dyn std::error::Error>> {
    let docpack_path = Path::new(path);

    // Check if path already exists
    if docpack_path.exists() {
        return Err(format!("Path already exists: {}", path).into());
    }

    println!("Initializing new .docpack at: {}", path);

    // Determine docpack name
    let docpack_name = name.unwrap_or_else(|| {
        docpack_path
            .file_name()
            .and_then(|n| n.to_str())
            .unwrap_or("my-docpack")
    });

    // Create directory structure
    println!("Creating directory structure...");
    fs::create_dir_all(docpack_path)?;
    fs::create_dir_all(docpack_path.join("files"))?;
    fs::create_dir_all(docpack_path.join("index"))?;
    fs::create_dir_all(docpack_path.join("output"))?;

    // Create docpack.json
    println!("Creating docpack.json...");
    let manifest = json!({
        "version": "1.0",
        "name": docpack_name,
        "description": "A new docpack",
        "environment": {
            "tools": [
                "list_files",
                "read_file",
                "write_output"
            ],
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
            "source_type": "manual",
            "language": "unknown"
        }
    });

    let manifest_path = docpack_path.join("docpack.json");
    let mut manifest_file = fs::File::create(&manifest_path)?;
    manifest_file.write_all(serde_json::to_string_pretty(&manifest)?.as_bytes())?;

    // Create tasks.json if requested
    if with_tasks {
        println!("Creating tasks.json...");
        let tasks = json!({
            "mission": "Explore and understand this project",
            "tasks": [
                {
                    "id": "task_1",
                    "name": "Create project overview",
                    "description": "Analyze the project structure and create a comprehensive overview",
                    "tools_allowed": ["list_files", "read_file", "write_output"],
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
            },
            "evaluation": {
                "success_criteria": [
                    "All tasks completed without errors",
                    "Output files exist at specified paths"
                ]
            }
        });

        let tasks_path = docpack_path.join("tasks.json");
        let mut tasks_file = fs::File::create(&tasks_path)?;
        tasks_file.write_all(serde_json::to_string_pretty(&tasks)?.as_bytes())?;
    }

    // Create README in files/
    println!("Creating placeholder README...");
    let readme_content = format!(
        "# {}\n\nAdd your project files to this directory.\n\nThis .docpack was created with localdoc-cli.\n",
        docpack_name
    );
    let readme_path = docpack_path.join("files").join("README.md");
    fs::write(readme_path, readme_content)?;

    println!("\n✓ Successfully initialized .docpack: {}", path);
    println!("\nNext steps:");
    println!("  1. Add your source files to {}/files/", path);
    println!("  2. Customize {}/docpack.json to enable additional tools", path);
    if with_tasks {
        println!("  3. Edit {}/tasks.json to define your documentation goals", path);
        println!("  4. Run: localdoc run {}", path);
    } else {
        println!("  3. Create {}/tasks.json to define your documentation goals", path);
        println!("  4. Run: localdoc run {}", path);
    }

    Ok(())
}

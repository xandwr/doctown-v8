use std::fs;
use std::path::Path;
use serde_json::Value;

pub fn run(docpack: &str) -> Result<(), Box<dyn std::error::Error>> {
    let docpack_path = Path::new(docpack);

    println!("Validating .docpack: {}\n", docpack);

    let mut errors = Vec::new();
    let mut warnings = Vec::new();

    // Check if path exists
    if !docpack_path.exists() {
        errors.push(format!("Path does not exist: {}", docpack));
        print_results(&errors, &warnings);
        return Err("Validation failed".into());
    }

    if !docpack_path.is_dir() {
        errors.push(format!("Path is not a directory: {}", docpack));
        print_results(&errors, &warnings);
        return Err("Validation failed".into());
    }

    // Check required directories
    let files_dir = docpack_path.join("files");
    let index_dir = docpack_path.join("index");
    let output_dir = docpack_path.join("output");

    if !files_dir.exists() {
        errors.push("Missing required directory: files/".to_string());
    }

    if !index_dir.exists() {
        warnings.push("Missing optional directory: index/".to_string());
    }

    if !output_dir.exists() {
        warnings.push("Missing output directory (will be created at runtime): output/".to_string());
    }

    // Check and validate docpack.json
    let manifest_path = docpack_path.join("docpack.json");
    if !manifest_path.exists() {
        errors.push("Missing required file: docpack.json".to_string());
    } else {
        match fs::read_to_string(&manifest_path) {
            Ok(content) => {
                match serde_json::from_str::<Value>(&content) {
                    Ok(manifest) => {
                        validate_manifest(&manifest, &mut errors, &mut warnings);
                    }
                    Err(e) => {
                        errors.push(format!("Invalid JSON in docpack.json: {}", e));
                    }
                }
            }
            Err(e) => {
                errors.push(format!("Cannot read docpack.json: {}", e));
            }
        }
    }

    // Check and validate tasks.json
    let tasks_path = docpack_path.join("tasks.json");
    if !tasks_path.exists() {
        warnings.push("Missing optional file: tasks.json (agent will run in exploration mode)".to_string());
    } else {
        match fs::read_to_string(&tasks_path) {
            Ok(content) => {
                match serde_json::from_str::<Value>(&content) {
                    Ok(tasks) => {
                        validate_tasks(&tasks, &mut warnings);
                    }
                    Err(e) => {
                        errors.push(format!("Invalid JSON in tasks.json: {}", e));
                    }
                }
            }
            Err(e) => {
                errors.push(format!("Cannot read tasks.json: {}", e));
            }
        }
    }

    // Check index files if index directory exists
    if index_dir.exists() {
        let search_path = index_dir.join("search.json");
        let graph_path = index_dir.join("graph.json");

        if search_path.exists() {
            match fs::read_to_string(&search_path) {
                Ok(content) => {
                    if let Err(e) = serde_json::from_str::<Value>(&content) {
                        errors.push(format!("Invalid JSON in index/search.json: {}", e));
                    }
                }
                Err(e) => {
                    warnings.push(format!("Cannot read index/search.json: {}", e));
                }
            }
        }

        if graph_path.exists() {
            match fs::read_to_string(&graph_path) {
                Ok(content) => {
                    if let Err(e) = serde_json::from_str::<Value>(&content) {
                        errors.push(format!("Invalid JSON in index/graph.json: {}", e));
                    }
                }
                Err(e) => {
                    warnings.push(format!("Cannot read index/graph.json: {}", e));
                }
            }
        }
    }

    print_results(&errors, &warnings);

    if !errors.is_empty() {
        Err("Validation failed".into())
    } else {
        println!("\n✓ Docpack is valid!");
        Ok(())
    }
}

fn validate_manifest(manifest: &Value, errors: &mut Vec<String>, warnings: &mut Vec<String>) {
    // Check version
    if manifest["version"].as_str().is_none() {
        errors.push("docpack.json: missing required field 'version'".to_string());
    }

    // Check name
    if manifest["name"].as_str().is_none() {
        warnings.push("docpack.json: missing recommended field 'name'".to_string());
    }

    // Check environment
    if manifest["environment"].is_null() {
        errors.push("docpack.json: missing required field 'environment'".to_string());
    } else {
        let env = &manifest["environment"];

        // Check tools
        if let Some(tools) = env["tools"].as_array() {
            let valid_tools = [
                "list_files",
                "read_file",
                "read_image",
                "read_pdf",
                "search_code",
                "query_graph",
                "write_output",
            ];

            for tool in tools {
                if let Some(tool_name) = tool.as_str() {
                    if !valid_tools.contains(&tool_name) {
                        warnings.push(format!(
                            "docpack.json: unknown tool '{}' (may not be supported)",
                            tool_name
                        ));
                    }
                }
            }
        } else {
            errors.push("docpack.json: 'environment.tools' must be an array".to_string());
        }
    }
}

fn validate_tasks(tasks: &Value, warnings: &mut Vec<String>) {
    // Check mission
    if tasks["mission"].as_str().is_none() {
        warnings.push("tasks.json: missing recommended field 'mission'".to_string());
    }

    // Check tasks array
    if let Some(task_list) = tasks["tasks"].as_array() {
        for (i, task) in task_list.iter().enumerate() {
            if task["name"].as_str().is_none() {
                warnings.push(format!("tasks.json: task {} missing 'name'", i));
            }
            if task["description"].as_str().is_none() {
                warnings.push(format!("tasks.json: task {} missing 'description'", i));
            }
        }
    } else {
        warnings.push("tasks.json: 'tasks' should be an array".to_string());
    }
}

fn print_results(errors: &[String], warnings: &[String]) {
    if !errors.is_empty() {
        println!("❌ Errors ({}):", errors.len());
        for error in errors {
            println!("  • {}", error);
        }
        println!();
    }

    if !warnings.is_empty() {
        println!("⚠️  Warnings ({}):", warnings.len());
        for warning in warnings {
            println!("  • {}", warning);
        }
        println!();
    }
}

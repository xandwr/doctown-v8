use wasm_bindgen::prelude::*;
use zip::ZipArchive;
use std::io::Cursor;
use serde::{Deserialize, Serialize};

#[wasm_bindgen]
extern "C" {
    #[wasm_bindgen(js_namespace = console)]
    fn log(s: &str);
}

#[derive(Serialize, Deserialize)]
pub struct ExtractedFile {
    pub path: String,
    pub data: Vec<u8>,
    pub filename: String,
}

#[wasm_bindgen]
pub struct ZipProcessor {
    files: Vec<ExtractedFile>,
}

#[wasm_bindgen]
impl ZipProcessor {
    #[wasm_bindgen(constructor)]
    pub fn new() -> ZipProcessor {
        ZipProcessor {
            files: Vec::new(),
        }
    }

    /// Extract all files from a zip archive
    /// Returns true if it's a valid docpack (has docpack.json), false if it's a regular zip
    #[wasm_bindgen]
    pub fn extract_zip(&mut self, zip_data: &[u8]) -> Result<bool, JsValue> {
        self.files.clear();

        let cursor = Cursor::new(zip_data);
        let mut archive = ZipArchive::new(cursor)
            .map_err(|e| JsValue::from_str(&format!("Failed to read zip: {}", e)))?;

        let mut is_docpack = false;

        // Extract all files
        for i in 0..archive.len() {
            let mut file = archive.by_index(i)
                .map_err(|e| JsValue::from_str(&format!("Failed to read file at index {}: {}", i, e)))?;

            let path = file.name().to_string();

            // Check if it's a docpack
            if path == "docpack.json" {
                is_docpack = true;
            }

            // Skip directories
            if file.is_dir() {
                continue;
            }

            // Read file data
            let mut data = Vec::new();
            std::io::copy(&mut file, &mut data)
                .map_err(|e| JsValue::from_str(&format!("Failed to read file data: {}", e)))?;

            // Extract filename from path
            let filename = path.split('/').last().unwrap_or(&path).to_string();

            self.files.push(ExtractedFile {
                path: path.clone(),
                data,
                filename,
            });
        }

        Ok(is_docpack)
    }

    /// Get the number of extracted files
    #[wasm_bindgen]
    pub fn file_count(&self) -> usize {
        self.files.len()
    }

    /// Get all extracted files as a JS value
    #[wasm_bindgen]
    pub fn get_files(&self) -> Result<JsValue, JsValue> {
        serde_wasm_bindgen::to_value(&self.files)
            .map_err(|e| JsValue::from_str(&format!("Serialization error: {}", e)))
    }

    /// Get a specific file by path
    #[wasm_bindgen]
    pub fn get_file_by_path(&self, path: &str) -> Result<JsValue, JsValue> {
        let file = self.files.iter()
            .find(|f| f.path == path)
            .ok_or_else(|| JsValue::from_str("File not found"))?;

        serde_wasm_bindgen::to_value(file)
            .map_err(|e| JsValue::from_str(&format!("Serialization error: {}", e)))
    }

    /// Check if a file exists with the given path
    #[wasm_bindgen]
    pub fn has_file(&self, path: &str) -> bool {
        self.files.iter().any(|f| f.path == path)
    }

    /// Get all file paths that start with a given prefix
    #[wasm_bindgen]
    pub fn get_files_with_prefix(&self, prefix: &str) -> Result<JsValue, JsValue> {
        let filtered: Vec<&ExtractedFile> = self.files.iter()
            .filter(|f| f.path.starts_with(prefix))
            .collect();

        serde_wasm_bindgen::to_value(&filtered)
            .map_err(|e| JsValue::from_str(&format!("Serialization error: {}", e)))
    }
}

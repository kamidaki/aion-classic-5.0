//! Carregador de strings oficiais do cliente Aion (`client_strings_item.xml`, etc.).
//! Suporta decodificação de arquivos XML em UTF-16LE e UTF-8.

use std::collections::HashMap;
use std::fs::File;
use std::io::Read;
use std::path::Path;

pub struct StringTable {
    strings: HashMap<String, String>,
}

impl StringTable {
    pub fn new() -> Self {
        Self {
            strings: HashMap::new(),
        }
    }

    pub fn get(&self, key: &str) -> Option<&str> {
        self.strings.get(key).map(|s| s.as_str())
    }

    pub fn insert(&mut self, key: String, val: String) {
        self.strings.insert(key, val);
    }

    pub fn len(&self) -> usize {
        self.strings.len()
    }

    pub fn is_empty(&self) -> bool {
        self.strings.is_empty()
    }

    /// Carrega e indexa um arquivo de strings XML (UTF-16LE ou UTF-8).
    pub fn load_file<P: AsRef<Path>>(&mut self, path: P) -> std::io::Result<usize> {
        let p = path.as_ref();
        if !p.exists() {
            return Ok(0);
        }

        let mut file = File::open(p)?;
        let mut buffer = Vec::new();
        file.read_to_end(&mut buffer)?;

        let content = if buffer.starts_with(&[0xFF, 0xFE]) {
            // UTF-16LE
            let u16_slice: &[u16] = unsafe {
                std::slice::from_raw_parts(
                    buffer[2..].as_ptr() as *const u16,
                    (buffer.len() - 2) / 2,
                )
            };
            String::from_utf16_lossy(u16_slice)
        } else if buffer.starts_with(&[0xEF, 0xBB, 0xBF]) {
            // UTF-8 BOM
            String::from_utf8_lossy(&buffer[3..]).into_owned()
        } else {
            // UTF-8 Padrão
            String::from_utf8_lossy(&buffer).into_owned()
        };

        let initial_count = self.strings.len();
        self.parse_content(&content);
        Ok(self.strings.len() - initial_count)
    }

    fn parse_content(&mut self, content: &str) {
        let mut pos = 0;
        while let Some(start_tag) = content[pos..].find("<string>") {
            let item_start = pos + start_tag;
            let end_tag = match content[item_start..].find("</string>") {
                Some(end) => item_start + end + 9,
                None => break,
            };

            let block = &content[item_start..end_tag];
            if let (Some(name_start), Some(body_start)) = (block.find("<name>"), block.find("<body>")) {
                if let (Some(name_end), Some(body_end)) = (block[name_start + 6..].find("</name>"), block[body_start + 6..].find("</body>")) {
                    let key = block[name_start + 6..name_start + 6 + name_end].trim().to_string();
                    let val = block[body_start + 6..body_start + 6 + body_end].trim().to_string();
                    if !key.is_empty() && !val.is_empty() {
                        self.strings.insert(key, val);
                    }
                }
            }

            pos = end_tag;
        }
    }
}

pub fn load_item_strings<P: AsRef<Path>>(strings_dir: P) -> StringTable {
    let mut table = StringTable::new();
    let dir = strings_dir.as_ref();

    let files = [
        "client_strings_item.xml",
        "client_strings_item2.xml",
    ];

    for fname in &files {
        let path = dir.join(fname);
        if path.exists() {
            if let Ok(count) = table.load_file(&path) {
                println!("INFO: Loaded {} item strings from {}", count, path.display());
            }
        }
    }

    table
}

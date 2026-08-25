use std::collections::HashMap;
use std::fs;
use std::path::Path;

#[derive(Debug, Clone, Default)]
pub struct Properties {
    entries: HashMap<String, String>,
}

impl Properties {
    pub fn new() -> Self {
        Self {
            entries: HashMap::new(),
        }
    }

    /// Loads and parses a Java-style .properties file from disk.
    pub fn load_from_file<P: AsRef<Path>>(path: P) -> std::io::Result<Self> {
        let content = fs::read_to_string(path)?;
        Ok(Self::parse(&content))
    }

    /// Parses a Java-style .properties formatted string.
    pub fn parse(content: &str) -> Self {
        let mut entries = HashMap::new();

        for line in content.lines() {
            let trimmed = line.trim();

            // Ignore empty lines and comments (# or !)
            if trimmed.is_empty() || trimmed.starts_with('#') || trimmed.starts_with('!') {
                continue;
            }

            // Find key-value delimiter (= or :)
            if let Some(pos) = trimmed.find(|c| c == '=' || c == ':') {
                let key = trimmed[..pos].trim().to_string();
                let value = trimmed[pos + 1..].trim().to_string();
                if !key.is_empty() {
                    entries.insert(key, value);
                }
            }
        }

        Self { entries }
    }

    #[inline]
    pub fn get_str(&self, key: &str) -> Option<&str> {
        self.entries.get(key).map(|s| s.as_str())
    }

    #[inline]
    pub fn get_string(&self, key: &str, default: &str) -> String {
        self.get_str(key).map(|s| s.to_string()).unwrap_or_else(|| default.to_string())
    }

    #[inline]
    pub fn get_bool(&self, key: &str, default: bool) -> bool {
        self.get_str(key)
            .map(|s| match s.to_lowercase().as_str() {
                "true" | "1" | "yes" | "on" | "enable" | "enabled" => true,
                "false" | "0" | "no" | "off" | "disable" | "disabled" => false,
                _ => default,
            })
            .unwrap_or(default)
    }

    #[inline]
    pub fn get_u16(&self, key: &str, default: u16) -> u16 {
        self.get_str(key).and_then(|s| s.parse::<u16>().ok()).unwrap_or(default)
    }

    #[inline]
    pub fn get_u32(&self, key: &str, default: u32) -> u32 {
        self.get_str(key).and_then(|s| s.parse::<u32>().ok()).unwrap_or(default)
    }

    #[inline]
    pub fn get_u64(&self, key: &str, default: u64) -> u64 {
        self.get_str(key).and_then(|s| s.parse::<u64>().ok()).unwrap_or(default)
    }

    #[inline]
    pub fn get_i32(&self, key: &str, default: i32) -> i32 {
        self.get_str(key).and_then(|s| s.parse::<i32>().ok()).unwrap_or(default)
    }

    #[inline]
    pub fn get_u8(&self, key: &str, default: u8) -> u8 {
        self.get_str(key).and_then(|s| s.parse::<u8>().ok()).unwrap_or(default)
    }

    #[inline]
    pub fn get_f32(&self, key: &str, default: f32) -> f32 {
        self.get_str(key).and_then(|s| s.parse::<f32>().ok()).unwrap_or(default)
    }

    #[inline]
    pub fn get_f64(&self, key: &str, default: f64) -> f64 {
        self.get_str(key).and_then(|s| s.parse::<f64>().ok()).unwrap_or(default)
    }

    #[inline]
    pub fn contains_key(&self, key: &str) -> bool {
        self.entries.contains_key(key)
    }

    #[inline]
    pub fn len(&self) -> usize {
        self.entries.len()
    }

    #[inline]
    pub fn is_empty(&self) -> bool {
        self.entries.is_empty()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_properties_parsing() {
        let sample = r#"
        # Header comment
        ! Another comment
        gameserver.network.port = 7777
        gameserver.server.name = Brasil em Chamas
        gameserver.rate.xp = 2.5
        gameserver.geodata.enable = true
        gameserver.country.code: 2
        "#;

        let props = Properties::parse(sample);
        assert_eq!(props.get_u16("gameserver.network.port", 0), 7777);
        assert_eq!(props.get_string("gameserver.server.name", ""), "Brasil em Chamas");
        assert_eq!(props.get_f32("gameserver.rate.xp", 1.0), 2.5);
        assert_eq!(props.get_bool("gameserver.geodata.enable", false), true);
        assert_eq!(props.get_u8("gameserver.country.code", 0), 2);
    }
}

//! Monitor de integridade e timestamp de arquivos (Hot-Reload de Cache).
//! Detecta modificações em arquivos XML e .properties e aciona recargas dinâmicas.

use std::collections::HashMap;
use std::path::{Path, PathBuf};
use std::time::SystemTime;

pub struct CacheWatcher {
    tracked_files: HashMap<PathBuf, SystemTime>,
}

impl CacheWatcher {
    pub fn new() -> Self {
        Self {
            tracked_files: HashMap::new(),
        }
    }

    /// Registra um arquivo para monitoramento contínuo.
    pub fn track_file<P: AsRef<Path>>(&mut self, path: P) {
        let p = path.as_ref().to_path_buf();
        if let Ok(metadata) = std::fs::metadata(&p) {
            if let Ok(modified) = metadata.modified() {
                self.tracked_files.insert(p, modified);
            }
        }
    }

    /// Verifica se algum dos arquivos monitorados foi alterado no disco.
    /// Retorna a lista de caminhos dos arquivos modificados.
    pub fn check_modifications(&mut self) -> Vec<PathBuf> {
        let mut modified_files = Vec::new();

        for (path, last_time) in self.tracked_files.iter_mut() {
            if let Ok(metadata) = std::fs::metadata(path) {
                if let Ok(current_time) = metadata.modified() {
                    if current_time > *last_time {
                        println!("INFO: Detected modification in {}", path.display());
                        *last_time = current_time;
                        modified_files.push(path.clone());
                    }
                }
            }
        }

        modified_files
    }

    /// Indica se houve qualquer alteração em arquivos de dados.
    pub fn has_changes(&mut self) -> bool {
        !self.check_modifications().is_empty()
    }
}

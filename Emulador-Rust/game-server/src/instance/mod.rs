//! Subsistema de Instâncias e Masmorras (InstanceEngine / InstanceService - Padrão Java Aion Classic 2.8 / 4.5)

pub mod handlers;
pub mod instance_engine;
pub mod models;
pub mod services;

#[cfg(test)]
pub mod tests;

// Re-exportações de modelos fundamentais e compatibilidade
pub use handlers::*;
pub use instance_engine::*;
pub use models::*;
pub use services::*;

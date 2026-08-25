//! Camada Geral de Rede e Protocolo do Aion Classic (Network Layer)
//!
//! Organizada em módulos especializados por domínio, seguindo o padrão clássico do Java:
//! - `opcodes`: Catálogo canônico de todos os códigos de operação CM e SM
//! - `crypt`: Criptografia Gameforge XOR e atualização de chaves
//! - `cm`: Todos os pacotes vindos do cliente (Client Messages), divididos por pastas de domínio
//! - `sm`: Todos os pacotes enviados ao cliente (Server Messages), divididos por pastas de domínio

pub mod opcodes;
pub mod crypt;
pub mod cm;
pub mod sm;

pub use opcodes::{cm as cm_opcodes, sm as sm_opcodes, PacketRegistry, PacketDefinition, PacketDirection};
pub use crypt::*;
pub use cm::ClientMessage;

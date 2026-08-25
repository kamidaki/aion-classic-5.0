//! Camada de Criptografia Gameforge XOR do Aion Classic

pub use commons::game::{decrypt, encrypt, gen_xor_key, gen_xor_seed};

pub const STATIC_HEADER_KEY: &[u8] = b"nKO/WctQ0AVLbpzfBkS6NevDYT8ourG5CRlmdjyJ72aswx4EPq1UgZhFMXH?3iI9";

pub fn update_key(key: &mut [u8; 8], size: usize) {
    let size_bytes = (size as u32).to_le_bytes();
    for i in 0..4 {
        key[i] = key[i].wrapping_add(size_bytes[i]);
    }
}

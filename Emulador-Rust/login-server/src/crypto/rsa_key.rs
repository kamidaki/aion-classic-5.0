//! RSA key generation, modulus scrambling, and raw credential decryption for Aion Classic

use rsa::traits::{PrivateKeyParts, PublicKeyParts};
use rsa::{BigUint, RsaPrivateKey};

#[derive(Clone)]
pub struct RsaManager {
    private_key: RsaPrivateKey,
    scrambled_modulus: [u8; 128],
}

impl RsaManager {
    pub fn new() -> Self {
        let mut rng = rand::thread_rng();
        let private_key = RsaPrivateKey::new(&mut rng, 1024).expect("Failed to generate RSA key");
        let modulus_biguint = private_key.n();
        let modulus_bytes = modulus_biguint.to_bytes_be();

        let mut n_128 = [0u8; 128];
        if modulus_bytes.len() >= 128 {
            n_128.copy_from_slice(&modulus_bytes[modulus_bytes.len() - 128..]);
        } else {
            let offset = 128 - modulus_bytes.len();
            n_128[offset..].copy_from_slice(&modulus_bytes);
        }

        let scrambled_modulus = Self::scramble_modulus(&n_128);
        Self {
            private_key,
            scrambled_modulus,
        }
    }

    pub fn get_scrambled_modulus(&self) -> &[u8; 128] {
        &self.scrambled_modulus
    }

    pub fn decrypt_credentials(&self, raw_128: &[u8]) -> Option<(String, String)> {
        if raw_128.len() < 128 {
            return None;
        }
        let c_biguint = BigUint::from_bytes_be(&raw_128[..128]);
        let d = self.private_key.d();
        let n = self.private_key.n();
        let m_biguint = c_biguint.modpow(d, n);
        let m_bytes = m_biguint.to_bytes_be();

        let mut dec = [0u8; 128];
        if m_bytes.len() >= 128 {
            dec.copy_from_slice(&m_bytes[m_bytes.len() - 128..]);
        } else {
            let offset = 128 - m_bytes.len();
            dec[offset..].copy_from_slice(&m_bytes);
        }

        // Standard Aion Classic: dec[64..96] is username, dec[96..128] is password
        let user_slice = &dec[64..96];
        let pass_slice = &dec[96..128];

        let user_null = user_slice
            .iter()
            .position(|&b| b == 0)
            .unwrap_or(user_slice.len());
        let pass_null = pass_slice
            .iter()
            .position(|&b| b == 0)
            .unwrap_or(pass_slice.len());

        let user = String::from_utf8_lossy(&user_slice[..user_null])
            .trim()
            .to_string();
        let pass = String::from_utf8_lossy(&pass_slice[..pass_null])
            .trim()
            .to_string();

        if !user.is_empty() {
            Some((user, pass))
        } else {
            None
        }
    }

    pub fn scramble_modulus(modulus: &[u8; 128]) -> [u8; 128] {
        let mut enc = *modulus;
        for i in 0..4 {
            let temp = enc[i];
            enc[i] = enc[0x4d + i];
            enc[0x4d + i] = temp;
        }

        for i in 0..0x40 {
            enc[i] ^= enc[0x40 + i];
        }

        for i in 0..4 {
            enc[0x0d + i] ^= enc[0x34 + i];
        }

        for i in 0..0x40 {
            enc[0x40 + i] ^= enc[i];
        }

        enc
    }
}

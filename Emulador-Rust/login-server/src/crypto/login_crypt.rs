//! Cryptographic engine for Aion Classic Login Protocol (SM_INIT, CM_LOGIN, SM_LOGIN_OK, etc.)

use super::BlowfishCipher;
use rand::Rng;

pub const STATIC_BLOWFISH_KEY: [u8; 16] = [
    0x6b, 0x60, 0xcb, 0x5b, 0x82, 0xce, 0x90, 0xb1,
    0xcc, 0x2b, 0x6c, 0x55, 0x6c, 0x6c, 0x6c, 0x6c,
];

pub struct LoginCryptEngine {
    current_key: [u8; 16],
    updated_key: bool,
    cipher: BlowfishCipher,
}

impl LoginCryptEngine {
    pub fn new() -> Self {
        Self {
            current_key: STATIC_BLOWFISH_KEY,
            updated_key: false,
            cipher: BlowfishCipher::new(&STATIC_BLOWFISH_KEY),
        }
    }

    pub fn update_key(&mut self, new_key: [u8; 16]) {
        // Java CryptEngine.updateKey(): apenas guarda a nova chave e reinicializa
        // o cipher Blowfish com ela para cifrar os proximos pacotes.
        // Isso e equivalente a criar um novo BlowfishCipher com a nova chave.
        self.current_key = new_key;
        self.cipher = BlowfishCipher::new(&new_key);
        self.updated_key = true;
    }

    pub fn encrypt_init(&mut self, raw: &[u8], new_blowfish_key: [u8; 16]) -> Vec<u8> {
        // Java CryptEngine.encrypt() para o PRIMEIRO pacote (updatedKey=false):
        //
        //   AionServerPacket.write():
        //     buf.putShort(0)       [0..2] header placeholder
        //     writeImpl(con)        [2..] conteudo: opcode + dados (177 bytes)
        //     buf.flip()            limit=179, pos=0
        //     buf.putShort(0)       sobrescreve [0..2]
        //     b = buf.slice()       slice começa em pos=2 → b[0..177] = conteudo
        //     con.encrypt(b)        chama crypt.encrypt(b.array(), b.arrayOffset()+b.pos(), b.limit()-b.pos())
        //                           = crypt.encrypt(data, offset=0, length=177)
        //
        //   CryptEngine.encrypt(data, offset=0, length=177):
        //     length += 4    → 181
        //     length += 4    → 185   (primeiro pacote)
        //     length += 8 - 185%8 = 7 → 192
        //     encXORPass(data, offset=0, length=192, random):
        //       stop = 192 - 8 = 184
        //       pos  = 4 + 0  = 4
        //       loop while pos < 184: XOR data[4, 8, ..., 180]
        //       ecx escrito em data[184..188]
        //     cipher.cipher(data, 0, 192)   → cifra data[0..192]
        //     cipher.updateKey(sessionKey)  → troca key
        //
        // O Rust recebe o raw (177 bytes = conteudo do writeImpl), zero-pad para 192,
        // aplica enc_xor_pass e Blowfish. Sem prefixo extra.

        let mut buffer = vec![0u8; 192];
        let copy_len = raw.len().min(192);
        buffer[..copy_len].copy_from_slice(&raw[..copy_len]);

        let xor_seed: u32 = rand::thread_rng().gen();
        Self::enc_xor_pass(&mut buffer, xor_seed);
        self.cipher.cipher(&mut buffer);
        self.update_key(new_blowfish_key);

        buffer
    }


    pub fn encrypt_packet(&self, raw: &[u8]) -> Vec<u8> {
        let length = raw.len();
        let pad = 8 - ((length + 4) % 8);
        let total_len = length + 4 + (if pad == 8 { 0 } else { pad });

        let mut buffer = vec![0u8; total_len];
        buffer[..length].copy_from_slice(raw);

        Self::append_checksum(&mut buffer, total_len);
        self.cipher.cipher(&mut buffer);

        buffer
    }

    pub fn decrypt_packet(&self, data: &mut [u8]) -> bool {
        if data.len() % 8 != 0 || data.len() < 8 {
            return false;
        }
        
        let mut session_data = data.to_vec();
        self.cipher.decipher(&mut session_data);
        data.copy_from_slice(&session_data);
        true
    }

    pub fn verify_checksum(data: &[u8]) -> bool {
        let length = data.len();
        if length % 4 != 0 || length <= 4 {
            return false;
        }

        let mut chksum = 0u32;
        for chunk in data.chunks_exact(4) {
            let val = u32::from_le_bytes(chunk.try_into().unwrap());
            chksum ^= val;
        }

        chksum == 0
    }

    pub fn append_checksum(raw: &mut [u8], total_len: usize) {
        let count = total_len - 4;
        let mut chksum = 0u32;

        for chunk in raw[..count].chunks_exact(4) {
            let val = u32::from_le_bytes(chunk.try_into().unwrap());
            chksum ^= val;
        }

        raw[count..total_len].copy_from_slice(&chksum.to_le_bytes());
    }

    fn enc_xor_pass(data: &mut [u8], key: u32) {
        let total = data.len();
        let blocos = (total - 8) / 4;
        let mut curr_key = key;

        for i in 1..blocos {
            let p = i * 4;
            let plain = u32::from_le_bytes(data[p..p + 4].try_into().unwrap());
            curr_key = curr_key.wrapping_add(plain);
            let cipher = plain ^ curr_key;
            data[p..p + 4].copy_from_slice(&cipher.to_le_bytes());
        }

        data[total - 8..total - 4].copy_from_slice(&curr_key.to_le_bytes());
    }

    pub fn scramble_modulus(modulus: &[u8]) -> [u8; 128] {
        let mut encrypted_modulus = [0u8; 128];
        if modulus.len() == 129 && modulus[0] == 0x00 {
            encrypted_modulus.copy_from_slice(&modulus[1..129]);
        } else if modulus.len() == 128 {
            encrypted_modulus.copy_from_slice(&modulus[..128]);
        } else if modulus.len() < 128 {
            let start = 128 - modulus.len();
            encrypted_modulus[start..128].copy_from_slice(modulus);
        }

        for i in 0..4 {
            let temp = encrypted_modulus[i];
            encrypted_modulus[i] = encrypted_modulus[0x4D + i];
            encrypted_modulus[0x4D + i] = temp;
        }

        for i in 0..0x40 {
            encrypted_modulus[i] ^= encrypted_modulus[0x40 + i];
        }

        for i in 0..4 {
            encrypted_modulus[0x0D + i] ^= encrypted_modulus[0x34 + i];
        }

        for i in 0..0x40 {
            encrypted_modulus[0x40 + i] ^= encrypted_modulus[i];
        }

        encrypted_modulus
    }
}

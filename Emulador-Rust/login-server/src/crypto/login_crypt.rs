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
        // Replica exatamente o Java CryptEngine.encrypt() para o PRIMEIRO pacote:
        //
        //   int length = buf.limit() - 2;   // tamanho do payload (sem os 2 bytes de header)
        //   final int offset = 2;            // posicao do payload no buffer completo
        //   length += 4;                     // +4 (checksum region)
        //   length += 4;                     // +4 extra para o primeiro pacote
        //   length += 8 - length % 8;        // alinhamento
        //   → length = 192 (payload de 177 bytes → 177+4+4 = 185 → arredonda para 192)
        //
        //   encXORPass(data, offset=2, length=192, randomKey)
        //   cipher.cipher(data, offset=2, length=192)
        //   cipher.updateKey(session_key)
        //
        // O buffer Java tem: [0..2] = header de tamanho, [2..194] = payload de 192 bytes.
        // O nosso buffer tem apenas os 192 bytes do payload (sem header).
        // Para replicar o XOR do Java, precisamos simular o offset=2.

        let mut buffer = vec![0u8; 192];
        let copy_len = raw.len().min(192);
        buffer[..copy_len].copy_from_slice(&raw[..copy_len]);

        let xor_seed: u32 = rand::thread_rng().gen();
        // enc_xor_pass com offset=2 (simula o buffer Java que inclui o header de 2 bytes)
        Self::enc_xor_pass_with_offset(&mut buffer, xor_seed, 2);

        // Cifra os 192 bytes com a static key
        self.cipher.cipher(&mut buffer);

        // Troca para a session key (para os proximos pacotes)
        self.update_key(new_blowfish_key);

        buffer
    }

    /// Replica exatamente o Java CryptEngine.encXORPass(data, offset, length, key).
    ///
    /// Java usa indices absolutos no buffer completo (que inclui o header de 2 bytes).
    /// O parametro `header_offset` simula esse offset: o XOR comeca em `header_offset + 4`
    /// e o stop e `length - 8` (onde length e o tamanho da regiao cifrada = 192).
    ///
    /// Java:
    ///   stop = length - 8  = 192 - 8 = 184  (indice absoluto no buffer Java)
    ///   pos  = 4 + offset  = 4 + 2   = 6    (indice absoluto no buffer Java)
    ///   loop: while pos < stop → processa [6, 10, 14, ..., 180] no buffer Java
    ///         → [4, 8, 12, ..., 178] no payload (subtraindo offset=2)
    ///   ecx escrito em pos=184 (absoluto) → payload[182..186]
    fn enc_xor_pass_with_offset(data: &mut [u8], key: u32, header_offset: usize) {
        // Simula: stop = length - 8, com length=192 (tamanho da regiao cifrada)
        // e pos_inicial = 4 + header_offset
        // Todos os indices sao relativos ao payload (data[]).
        // Convertendo: pos_payload = pos_absoluto - header_offset
        //   pos_inicial_payload = (4 + header_offset) - header_offset = 4
        //   stop_absoluto = 192 - 8 = 184
        //   stop_payload  = 184 - header_offset = 184 - 2 = 182

        let stop_payload = (192usize - 8).saturating_sub(header_offset); // 182
        let mut curr_key = key;
        let mut pos = 4usize; // inicio no payload

        while pos < stop_payload {
            let plain = u32::from_le_bytes(data[pos..pos + 4].try_into().unwrap());
            curr_key = curr_key.wrapping_add(plain);
            let cipher_val = plain ^ curr_key;
            data[pos..pos + 4].copy_from_slice(&cipher_val.to_le_bytes());
            pos += 4;
        }

        // Escreve a seed final: em pos_absoluto=184 → payload[184-2=182]
        let key_pos_payload = 184usize.saturating_sub(header_offset); // 182
        data[key_pos_payload..key_pos_payload + 4].copy_from_slice(&curr_key.to_le_bytes());
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
        if Self::verify_checksum(&session_data) {
            data.copy_from_slice(&session_data);
            return true;
        }

        let static_cipher = BlowfishCipher::new(&STATIC_BLOWFISH_KEY);
        let mut static_data = data.to_vec();
        static_cipher.decipher(&mut static_data);
        if Self::verify_checksum(&static_data) {
            data.copy_from_slice(&static_data);
            return true;
        }

        data.copy_from_slice(&session_data);
        false
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
        let total_len = data.len();
        let ecx = (total_len - 8) / 4;
        let mut curr_key = key;

        for i in 1..ecx {
            let p = i * 4;
            let plain = u32::from_le_bytes(data[p..p + 4].try_into().unwrap());
            curr_key = curr_key.wrapping_add(plain);
            let cipher = plain ^ curr_key;
            data[p..p + 4].copy_from_slice(&cipher.to_le_bytes());
        }

        let key_offset = total_len - 8;
        data[key_offset..key_offset + 4].copy_from_slice(&curr_key.to_le_bytes());
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

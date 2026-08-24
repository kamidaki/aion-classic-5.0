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

#[cfg(test)]
mod test {
    use super::*;

    /// Desfaz o [`RsaManager::scramble_modulus`].
    ///
    /// E o que o cliente faz com os 128 bytes que vem no `SM_INIT` para recuperar o modulo RSA de
    /// verdade, sem o qual ele nao consegue cifrar as credenciais. Cada passo do embaralhamento e
    /// um XOR ou uma troca, entao o inverso e a mesma sequencia ao contrario.
    fn desembaralha_modulo(embaralhado: &[u8; 128]) -> [u8; 128] {
        let mut m = *embaralhado;

        for i in 0..0x40 {
            m[0x40 + i] ^= m[i];
        }
        for i in 0..4 {
            m[0x0d + i] ^= m[0x34 + i];
        }
        for i in 0..0x40 {
            m[i] ^= m[0x40 + i];
        }
        for i in 0..4 {
            m.swap(i, 0x4d + i);
        }

        m
    }

    /// Monta o bloco de 128 bytes que o cliente cifra: usuario em [64..96], senha em [96..128].
    fn bloco_de_credenciais(usuario: &str, senha: &str) -> [u8; 128] {
        let mut b = [0u8; 128];
        b[64..64 + usuario.len()].copy_from_slice(usuario.as_bytes());
        b[96..96 + senha.len()].copy_from_slice(senha.as_bytes());
        b
    }

    /// Cifra como o cliente cifra: RSA cru, `c = m^65537 mod n`, sem padding.
    fn cifra_como_o_cliente(bloco: &[u8; 128], modulo: &[u8; 128]) -> Vec<u8> {
        let n = BigUint::from_bytes_be(modulo);
        let e = BigUint::from(65_537u32);
        let c = BigUint::from_bytes_be(bloco).modpow(&e, &n);

        let bytes = c.to_bytes_be();
        let mut saida = vec![0u8; 128];
        let inicio = 128 - bytes.len().min(128);
        saida[inicio..].copy_from_slice(&bytes[bytes.len() - (128 - inicio)..]);
        saida
    }

    #[test]
    fn o_embaralhamento_do_modulo_e_reversivel() {
        // Se nao fosse, o cliente nao teria como recuperar o modulo e nunca conseguiria cifrar as
        // credenciais -- o login pararia no CM_LOGIN sem nenhuma mensagem de erro.
        let mut original = [0u8; 128];
        for (i, b) in original.iter_mut().enumerate() {
            *b = (i as u8).wrapping_mul(7) ^ 0x3C;
        }

        let embaralhado = RsaManager::scramble_modulus(&original);
        assert_ne!(embaralhado, original, "o embaralhamento tem que mudar os bytes");
        assert_eq!(desembaralha_modulo(&embaralhado), original);
    }

    #[test]
    fn o_cliente_recupera_o_modulo_que_veio_no_sm_init() {
        // O modulo desembaralhado precisa ser o `n` real da chave do servidor: e com ele que o
        // cliente cifra. Confere-se pelo expoente -- se `n` estivesse errado, o modpow devolveria
        // um valor que o servidor nao consegue abrir, e o teste seguinte falharia.
        let rsa = RsaManager::new();
        let recuperado = desembaralha_modulo(rsa.get_scrambled_modulus());

        assert_eq!(recuperado.len(), 128, "modulo de 1024 bits");
        assert_ne!(recuperado, [0u8; 128]);
        assert_ne!(
            &recuperado[..],
            &rsa.get_scrambled_modulus()[..],
            "o que viaja na rede e a forma embaralhada"
        );
    }

    #[test]
    fn credenciais_cifradas_pelo_cliente_abrem_no_servidor() {
        // O caminho inteiro do CM_LOGIN, ponta a ponta:
        //   servidor gera a chave -> embaralha o modulo -> manda no SM_INIT
        //   cliente desembaralha -> cifra usuario e senha -> manda o CM_LOGIN
        //   servidor decifra com a chave privada
        let rsa = RsaManager::new();

        let modulo = desembaralha_modulo(rsa.get_scrambled_modulus());
        let bloco = bloco_de_credenciais("jogador1", "senha123");
        let cifrado = cifra_como_o_cliente(&bloco, &modulo);

        assert_eq!(cifrado.len(), 128);
        assert_ne!(&cifrado[64..96], &bloco[64..96], "tem que sair cifrado mesmo");

        let (usuario, senha) = rsa
            .decrypt_credentials(&cifrado)
            .expect("o servidor precisa abrir as credenciais");
        assert_eq!(usuario, "jogador1");
        assert_eq!(senha, "senha123");
    }

    #[test]
    fn credenciais_com_o_modulo_errado_nao_abrem() {
        // Guarda: se o cliente usasse o modulo embaralhado sem desfazer o embaralhamento -- ou se
        // o embaralhamento mudasse -- o servidor nao poderia recuperar nada.
        let rsa = RsaManager::new();
        let bloco = bloco_de_credenciais("jogador1", "senha123");

        // Cifra com a forma embaralhada, que nao e o `n` da chave.
        let cifrado = cifra_como_o_cliente(&bloco, rsa.get_scrambled_modulus());

        match rsa.decrypt_credentials(&cifrado) {
            None => {}
            Some((usuario, _)) => assert_ne!(
                usuario, "jogador1",
                "com o modulo errado nao pode sair a credencial certa"
            ),
        }
    }

    #[test]
    fn usuario_vazio_e_recusado() {
        let rsa = RsaManager::new();
        let modulo = desembaralha_modulo(rsa.get_scrambled_modulus());
        let cifrado = cifra_como_o_cliente(&bloco_de_credenciais("", ""), &modulo);

        assert_eq!(rsa.decrypt_credentials(&cifrado), None);
    }
}

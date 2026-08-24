//! Enquadramento do STS (porta 6600).
//!
//! E um protocolo tipo HTTP, com cabecalhos de uma letra. Formato confirmado nas capturas de
//! 21/08 e 23/08 de 2026, identico nas duas:
//!
//! ```text
//! pedido:    POST /Auth/LoginTokenStart STS/1.0\r\n s:1\r\n l:90\r\n \r\n <Request>...
//! resposta:  STS/1.0 200 OK\r\n l:863\r\n s:1R\r\n \r\n <Reply>...
//! ```
//!
//! Dois detalhes que a implementacao anterior errava:
//!
//! * a sequencia da resposta **ecoa a do pedido**, com um `R` colado -- nao e um numero fixo por
//!   rota;
//! * `l:` vem antes de `s:` na resposta e depois na pergunta.
//!
//! O `/Sts/Connect` chega **sem** cabecalho `s:` e o servidor oficial nao responde nada a ele.

use quick_xml::de::from_str;
use quick_xml::se::to_string;
use serde::{Deserialize, Serialize};

/// Um pedido do cliente, ja separado em rota, sequencia e corpo.
#[derive(Debug, PartialEq, Eq, Clone)]
pub struct StsRequest {
    pub path: String,
    /// Valor do cabecalho `s:`. Ausente no `/Sts/Connect`.
    pub seq: Option<u32>,
    pub body: Vec<u8>,
}

impl StsRequest {
    /// Le um pedido inteiro do buffer. Devolve `None` enquanto faltar byte.
    ///
    /// O segundo item e quantos bytes foram consumidos.
    pub fn parse(buf: &[u8]) -> Option<(Self, usize)> {
        let header_end = buf.windows(4).position(|w| w == b"\r\n\r\n")?;
        let header_str = std::str::from_utf8(&buf[..header_end]).ok()?;

        let mut linhas = header_str.lines();
        let inicial = linhas.next()?;
        // "POST /Auth/LoginTokenStart STS/1.0"
        let path = inicial.split_whitespace().nth(1).unwrap_or("/Sts/Ping").to_string();

        let mut content_len = 0usize;
        let mut seq = None;
        for linha in linhas {
            if let Some(v) = linha.strip_prefix("l:") {
                content_len = v.trim().parse().unwrap_or(0);
            } else if let Some(v) = linha.strip_prefix("s:") {
                seq = v.trim().parse().ok();
            }
        }

        let body_start = header_end + 4;
        if buf.len() < body_start + content_len {
            return None;
        }

        Some((
            Self {
                path,
                seq,
                body: buf[body_start..body_start + content_len].to_vec(),
            },
            body_start + content_len,
        ))
    }
}

/// Monta a resposta com o cabecalho na ordem que o servidor oficial usa.
pub fn encode_reply(body: &str, seq: u32) -> Vec<u8> {
    let mut out = format!("STS/1.0 200 OK\r\nl:{}\r\ns:{}R\r\n\r\n", body.len(), seq).into_bytes();
    out.extend_from_slice(body.as_bytes());
    out
}

pub fn deserialize_xml<'a, T: Deserialize<'a>>(xml: &'a str) -> Result<T, quick_xml::DeError> {
    from_str(xml)
}

pub fn serialize_xml<T: Serialize>(val: &T) -> Result<String, quick_xml::DeError> {
    to_string(val)
}

#[cfg(test)]
mod test {
    use super::*;

    /// Pedido copiado byte a byte da captura de 21/08. O corpo fecha em `\r\n`, e por isso `l:90`
    /// e nao 88.
    const PEDIDO_LOGIN_TOKEN_START: &[u8] = b"POST /Auth/LoginTokenStart STS/1.0\r\ns:1\r\nl:90\r\n\r\n<Request><ClientRand>nnjXtxKIAD8HFWOTxaDg7ns4rtabwqf3KKwfA24fwtU=</ClientRand></Request>\r\n";

    #[test]
    fn le_o_pedido_da_captura() {
        let (req, lido) = StsRequest::parse(PEDIDO_LOGIN_TOKEN_START).expect("pedido completo");
        assert_eq!(req.path, "/Auth/LoginTokenStart");
        assert_eq!(req.seq, Some(1));
        assert_eq!(req.body.len(), 90, "o tamanho tem que bater com o l: da captura");
        assert_eq!(lido, PEDIDO_LOGIN_TOKEN_START.len());
        assert!(req.body.starts_with(b"<Request><ClientRand>"));
        assert!(req.body.ends_with(b"</Request>\r\n"));
    }

    #[test]
    fn connect_chega_sem_sequencia() {
        // A rota que o cliente abre primeiro nao traz `s:`.
        let bruto = b"POST /Sts/Connect STS/1.0\r\nl:9\r\n\r\n<Connect/>";
        let (req, _) = StsRequest::parse(bruto).expect("pedido completo");
        assert_eq!(req.path, "/Sts/Connect");
        assert_eq!(req.seq, None, "o Connect da captura nao tem cabecalho s:");
    }

    #[test]
    fn pedido_incompleto_espera_mais_bytes() {
        let parcial = &PEDIDO_LOGIN_TOKEN_START[..PEDIDO_LOGIN_TOKEN_START.len() - 10];
        assert_eq!(StsRequest::parse(parcial), None);
        assert_eq!(StsRequest::parse(b"POST /Sts/Connect STS/1.0\r\n"), None);
    }

    #[test]
    fn dois_pedidos_colados_saem_um_a_um() {
        let mut juntos = PEDIDO_LOGIN_TOKEN_START.to_vec();
        juntos.extend_from_slice(b"POST /Sts/Ping STS/1.0\r\ns:7\r\nl:0\r\n\r\n");

        let (primeiro, lido) = StsRequest::parse(&juntos).unwrap();
        assert_eq!(primeiro.path, "/Auth/LoginTokenStart");
        let (segundo, _) = StsRequest::parse(&juntos[lido..]).unwrap();
        assert_eq!(segundo.path, "/Sts/Ping");
        assert_eq!(segundo.seq, Some(7));
    }

    #[test]
    fn cabecalho_da_resposta_bate_com_a_captura() {
        // A resposta ao TokenKeyData na captura: l:9, s:2R, corpo "<Reply/>\n".
        let bytes = encode_reply("<Reply/>\n", 2);
        assert_eq!(
            String::from_utf8_lossy(&bytes),
            "STS/1.0 200 OK\r\nl:9\r\ns:2R\r\n\r\n<Reply/>\n"
        );
    }
}

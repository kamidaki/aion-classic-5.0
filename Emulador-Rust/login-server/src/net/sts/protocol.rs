use quick_xml::de::from_str;
use quick_xml::se::to_string;
use serde::{Deserialize, Serialize};

#[derive(Debug, PartialEq, Eq, Clone)]
pub struct StsFrame {
    pub body: Vec<u8>,
}

impl StsFrame {
    pub fn parse(buf: &[u8]) -> Option<(Self, usize)> {
        // Look for \r\n\r\n header delimiter
        let header_end = buf.windows(4).position(|w| w == b"\r\n\r\n")?;
        let header_bytes = &buf[..header_end];
        let header_str = std::str::from_utf8(header_bytes).ok()?;

        let mut content_len: Option<usize> = None;
        for line in header_str.lines() {
            if let Some(val) = line.strip_prefix("l:") {
                if let Ok(l) = val.trim().parse::<usize>() {
                    content_len = Some(l);
                }
            }
        }

        let body_start = header_end + 4;
        let len = content_len.unwrap_or(0);
        if buf.len() < body_start + len {
            return None;
        }

        let body = buf[body_start..body_start + len].to_vec();
        Some((Self { body }, body_start + len))
    }

    pub fn encode(&self, seq: u32) -> Vec<u8> {
        let header = format!("STS/1.0 200 OK\r\nl:{}\r\ns:{}R\r\n\r\n", self.body.len(), seq);
        let mut out = header.into_bytes();
        out.extend_from_slice(&self.body);
        out
    }
}

pub fn deserialize_xml<'a, T: Deserialize<'a>>(xml: &'a str) -> Result<T, quick_xml::DeError> {
    from_str(xml)
}

pub fn serialize_xml<T: Serialize>(val: &T) -> Result<String, quick_xml::DeError> {
    to_string(val)
}

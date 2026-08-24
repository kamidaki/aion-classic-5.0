mod protocol;
use std::{
    io::{Read, Write},
    net::TcpStream,
    str::from_utf8,
    sync::Arc,
};

use crate::db::Db;
use crate::error::{Error, Result};
use krypt::sts::{Krypt, Rsa};
use protocol::Request;

const RECV_BUFFER_LEN: usize = 1024 * 64;
const SEND_BUFFER_LEN: usize = 1024 * 64;

pub struct Session {
    pub krypt: Krypt,
    pub authn_token: String,
    pub db: Arc<Db>,
}

impl Session {
    pub fn new(db: Arc<Db>) -> Self {
        let rsa_bits = 0x800;
        Self {
            krypt: Krypt {
                rsa: Rsa::new(rsa_bits),
                rc4: None,
                // TODO: Make random
                server_rand: *b"foofoofoofoofoofoofoofoofoofoofo",
                client_rand: [0u8; 0x20],
            },
            authn_token: String::new(),
            db,
        }
    }
    pub fn handle(mut self, mut stream: TcpStream) -> Result<()> {
        let mut requests: Vec<Request> = Vec::with_capacity(20);

        // Unencrypted loop
        loop {
            let mut recv_buffer = [0u8; RECV_BUFFER_LEN];
            let len = stream
                .read(&mut recv_buffer)
                .map_err(Error::ReadingFromSocket)?;

            self.parse_packets(&recv_buffer[..len], &mut requests)?;

            for request in requests.drain(..) {
                let mut send_buffer = [0u8; SEND_BUFFER_LEN];
                let len = request.handle(&mut self, &mut send_buffer);
                if len != 0 {
                    println!("DEBUG: Sending message");
                    println!("{}", from_utf8(&send_buffer[..len]).unwrap());
                    stream
                        .write(&send_buffer[..len])
                        .map_err(Error::WritingToSocket)?;
                }
            }

            // If we have enabled RC4 move on to the encrypted loop
            if self.krypt.rc4.is_some() {
                break;
            }
        }

        // Encrypted loop
        let mut rc4 = self.krypt.rc4.take().unwrap();
        loop {
            let mut recv_buf = [0u8; RECV_BUFFER_LEN];
            let len = stream
                .read(&mut recv_buf)
                .map_err(Error::ReadingFromSocket)?;
            rc4.decrypt(&mut recv_buf[..len]);

            self.parse_packets(&recv_buf[..len], &mut requests)?;

            for request in requests.drain(..) {
                let logout = request.is_logout();
                let mut send_buf = [0u8; SEND_BUFFER_LEN];
                let len = request.handle(&mut self, &mut send_buf);
                if len != 0 {
                    println!("DEBUG: Sending message");
                    println!("{}", from_utf8(&send_buf[..len]).unwrap());
                    rc4.encrypt(&mut send_buf[..len]);
                    match stream.write(&send_buf[..len]) {
                        Ok(_) => {}
                        Err(_) if logout => return Ok(()),
                        Err(e) => return Err(Error::WritingToSocket(e)),
                    }
                }
                if logout {
                    return Ok(());
                }
            }
        }
    }

    /// There can be one more more message in a packet
    fn parse_packets(&mut self, mut buffer: &[u8], requests: &mut Vec<Request>) -> Result<()> {
        loop {
            let (message, len) = Request::deserialise(buffer)?;
            requests.push(message);

            let remaining_bytes = buffer.len().checked_sub(len);
            match remaining_bytes {
                Some(0) => return Ok(()),
                Some(_) => buffer = &buffer[len..],
                None => return Err(Error::PacketLenOverflow),
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn deserialise_connect() {
        const PAYLOAD: &str = "POST /Sts/Connect STS/1.0\r\n\
            l:222\r\n\r\n\
            <Connect> <ConnType>400</ConnType> \
            <AppIndex>1</AppIndex> <Build>1001</Build> <ProductType>1020\
            </ProductType> <Address>69.69.69.69</Address> <Process>28025\
            </Process> <Epoch>7205</Epoch> <Program>3092</Program> </Connect>\
            \r\n";

        let db = std::sync::Arc::new(Db::open(":memory:").unwrap());
        let mut session = Session::new(db);
        let mut requests = Vec::new();
        session
            .parse_packets(PAYLOAD.as_bytes(), &mut requests)
            .unwrap();
    }

    #[test]
    fn deserialise_connect_len_too_short() {
        const PAYLOAD: &str = "POST /Sts/Connect STS/1.0\r\n\
            l:221\r\n\r\n\
            <Connect> <ConnType>400</ConnType> \
            <AppIndex>1</AppIndex> <Build>1001</Build> <ProductType>1020\
            </ProductType> <Address>69.69.69.69</Address> <Process>28025\
            </Process> <Epoch>7205</Epoch> <Program>3092</Program> </Connect>\
            \r\n";

        let db = std::sync::Arc::new(Db::open(":memory:").unwrap());
        let mut session = Session::new(db);
        let mut requests = Vec::new();
        assert!(matches!(
            session.parse_packets(PAYLOAD.as_bytes(), &mut requests),
            Err(_)
        ));
    }

    #[test]
    fn deserialise_login_token_start() {
        const PAYLOAD:&str = "POST /Auth/LoginTokenStart STS/1.0\r\n\
          s:1\r\n\
          l:90\r\n\r\n\
          <Request><ClientRand>5e+U2ifE4U0N+pFGggUkd94xrvvrsKzzFej1j2c7L5Y=</ClientRand></Request>\r\n";

        let db = std::sync::Arc::new(Db::open(":memory:").unwrap());
        let mut session = Session::new(db);
        let mut requests = Vec::new();
        session
            .parse_packets(PAYLOAD.as_bytes(), &mut requests)
            .unwrap();
    }

    #[test]
    fn deserialise_login_token_start_len_too_long() {
        const PAYLOAD:&str = "POST /Auth/LoginTokenStart STS/1.0\r\n\
          s:1\r\n\
          l:91\r\n\r\n\
          <Request><ClientRand>5e+U2ifE4U0N+pFGggUkd94xrvvrsKzzFej1j2c7L5Y=</ClientRand></Request>\r\n";

        let db = std::sync::Arc::new(Db::open(":memory:").unwrap());
        let mut session = Session::new(db);
        let mut requests = Vec::new();
        assert!(matches!(
            session.parse_packets(PAYLOAD.as_bytes(), &mut requests),
            Err(Error::PacketLenOverflow)
        ));
    }

    #[test]
    fn deserialise_concat() {
        const PAYLOAD: &str = "POST /Sts/Connect STS/1.0\r\n\
            l:222\r\n\r\n\
            <Connect> <ConnType>400</ConnType> \
            <AppIndex>1</AppIndex> <Build>1001</Build> <ProductType>1020\
            </ProductType> <Address>69.69.69.69</Address> <Process>28025\
            </Process> <Epoch>7205</Epoch> <Program>3092</Program> </Connect>\
            \r\n\
            POST /Auth/LoginTokenStart STS/1.0\r\n\
            s:1\r\n\
            l:90\r\n\r\n\
            <Request><ClientRand>5e+U2ifE4U0N+pFGggUkd94xrvvrsKzzFej1j2c7L5Y=</ClientRand></Request>\r\n";

        let db = std::sync::Arc::new(Db::open(":memory:").unwrap());
        let mut session = Session::new(db);
        let mut requests = Vec::new();
        session
            .parse_packets(PAYLOAD.as_bytes(), &mut requests)
            .unwrap();
    }

    #[test]
    fn deserialise_token_data_start() {
        const PAYLOAD:&str = "POST /Auth/TokenKeyData STS/1.0\r\ns:2\r\nl:1175\r\n\r\n<Request><EncryptionAlgorithm>AES</EncryptionAlgorithm><EncryptionKey>6e5Cr6CJt9qQlTrAUvlgXFwBhEN1XuL6jDIN0YjygTSeSd7q1YbuOdflnt5Jhd3HlPAIO255XcyPzFrdbLQqHbTU43VYJQP6Mh5reyLFSwpnXPQ1NOpDLGB55IVbmpsCWXljWZLLv1WsG8YGtpDyugcgtEkl93ampXQsymgRGJeQdaRijlaiNN0x7hkyd5Jiy2DbSHBQi0ZFGOmbqXJWvz44Sk7z2cZdsMlwvxjC5e1aftLMQCsXxjaCjA0a096p4UOeNjxX9SJYqX21iu6FbV9GqAhuugBY4lErof8T0gjcPAKkUjUam4dhztaeq3iVHcZNrGU3Ya05RvNJSmOZ5a==</EncryptionKey><PremasterSecret>RGHiUBPYb03kz3OprgfPgAKRQyDHFNbiOuvM8UrXvf1JKM15fyB85iSsyUQkdk8Z</PremasterSecret><AuthnToken>KwfobiQm1RjVyDpaBPeU3j04a632BamHjvQOx5GHCrSMClictcZSGEIPsRnDkh55Lh2L2IK5hLbq2VejEESJoJ0avallkElflKzr8lCn48AnemMhrV8H5NgqJTqUQnRd1G7kOZJedjanqmIY5Md3Bm5mbkfIUUT5i5Zf8ghhiGJuJLF19mEIiMDTI7kqTyvzkKog3MYuaYeC8AyodHTQXjRD9VWtTh9xCIaaiX5satDdEM91SfGA2hN8C4CeOfdvoVPlvPn3RnFCRWIhrxVse9BkhhE0TdzY5ba3iZBwKMJL8VFbJhNKDgMNIYY8mQmQPTdq7zhWmoUDgTXzOQm3iIcWEMdCqXQlNd2tO71idBAdkQIhblxd1tAS1FH7biGcudAX4OZiOeRfYyHnYIJUDmDd8Lt79WhXjXPO5iynzXQqanEFYu88wnAUay1sN7FaJY2lOAMPgG8BX4Dy5ZLnzvl0K6qRxMWkbiJIcFdfQO5G5hLC72H8n0p1laH2uxZt</AuthnToken><AuthProviderCode>gameforge</AuthProviderCode><AppId>5B4503FA-8521-4608-BB60-5CFAC87BD63A</AppId></Request>\r\n";

        let db = std::sync::Arc::new(Db::open(":memory:").unwrap());
        let mut session = Session::new(db);
        let mut requests = Vec::new();
        session
            .parse_packets(PAYLOAD.as_bytes(), &mut requests)
            .unwrap();
    }
}

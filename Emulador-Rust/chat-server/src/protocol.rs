use bytes::{Buf, BufMut, BytesMut};

#[derive(Debug)]
pub enum ChatClientPacket {
    Init { client_version: u32 },
    PlayerAuth { player_id: u32, token: String },
    ChannelJoin { channel_id: u32 },
    ChannelLeave { channel_id: u32 },
    ChannelMessage { channel_id: u32, message: String },
    Ping,
    Unknown(u8),
}

impl ChatClientPacket {
    pub fn parse(mut buf: &[u8]) -> Option<Self> {
        if buf.len() < 3 {
            return None;
        }

        let _len = buf.get_u16_le();
        let opcode = buf.get_u8();

        match opcode {
            0x01 => {
                if buf.remaining() >= 4 {
                    let version = buf.get_u32_le();
                    Some(ChatClientPacket::Init { client_version: version })
                } else {
                    Some(ChatClientPacket::Init { client_version: 1 })
                }
            }
            0x02 => {
                if buf.remaining() >= 4 {
                    let player_id = buf.get_u32_le();
                    let token = String::from_utf8_lossy(buf).trim_matches('\0').to_string();
                    Some(ChatClientPacket::PlayerAuth { player_id, token })
                } else {
                    None
                }
            }
            0x03 => {
                if buf.remaining() >= 4 {
                    let channel_id = buf.get_u32_le();
                    Some(ChatClientPacket::ChannelJoin { channel_id })
                } else {
                    None
                }
            }
            0x04 => {
                if buf.remaining() >= 4 {
                    let channel_id = buf.get_u32_le();
                    Some(ChatClientPacket::ChannelLeave { channel_id })
                } else {
                    None
                }
            }
            0x05 => {
                if buf.remaining() >= 4 {
                    let channel_id = buf.get_u32_le();
                    let message = String::from_utf8_lossy(buf).trim_matches('\0').to_string();
                    Some(ChatClientPacket::ChannelMessage { channel_id, message })
                } else {
                    None
                }
            }
            0x06 => Some(ChatClientPacket::Ping),
            op => Some(ChatClientPacket::Unknown(op)),
        }
    }
}

pub struct ChatServerPackets;

impl ChatServerPackets {
    pub fn sm_chat_ini() -> Vec<u8> {
        let mut buf = BytesMut::with_capacity(7);
        buf.put_u16_le(7);
        buf.put_u8(0x01); // Opcode SM_CHAT_INI
        buf.put_u32_le(0); // Status OK
        buf.to_vec()
    }

    pub fn sm_player_auth_response(success: bool) -> Vec<u8> {
        let mut buf = BytesMut::with_capacity(4);
        buf.put_u16_le(4);
        buf.put_u8(0x02); // Opcode SM_PLAYER_AUTH_RESPONSE
        buf.put_u8(if success { 1 } else { 0 });
        buf.to_vec()
    }

    pub fn sm_channel_response(channel_id: u32, success: bool) -> Vec<u8> {
        let mut buf = BytesMut::with_capacity(8);
        buf.put_u16_le(8);
        buf.put_u8(0x03); // Opcode SM_CHANNEL_RESPONSE
        buf.put_u32_le(channel_id);
        buf.put_u8(if success { 1 } else { 0 });
        buf.to_vec()
    }

    pub fn sm_channel_message(channel_id: u32, sender_name: &str, message: &str) -> Vec<u8> {
        let name_bytes = sender_name.as_bytes();
        let msg_bytes = message.as_bytes();
        let len = 3 + 4 + (name_bytes.len() + 1) + (msg_bytes.len() + 1);

        let mut buf = BytesMut::with_capacity(len);
        buf.put_u16_le(len as u16);
        buf.put_u8(0x04); // Opcode SM_CHANNEL_MESSAGE
        buf.put_u32_le(channel_id);
        buf.put_slice(name_bytes);
        buf.put_u8(0);
        buf.put_slice(msg_bytes);
        buf.put_u8(0);
        buf.to_vec()
    }
}

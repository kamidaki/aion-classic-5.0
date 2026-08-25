//! Pacote CM_SEND_MAIL

#[derive(Debug, Clone)]
pub struct CmSendMail {
    pub recipient_name: String,
    pub title: String,
    pub message: String,
    pub attached_item_obj_id: Option<u32>,
    pub attached_item_count: u64,
    pub attached_kinah: u64,
    pub is_express: bool,
}

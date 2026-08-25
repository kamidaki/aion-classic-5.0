//! Pacotes do Cliente para Correio e Mensagens (CM_MAIL_* - Padrão Classic 4.5)

#[derive(Debug, Clone)]
pub struct CmReadMail {
    pub mail_id: u32,
}

#[derive(Debug, Clone)]
pub struct CmReadExpressMail {
    pub mail_id: u32,
}

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

#[derive(Debug, Clone)]
pub struct CmDeleteMail {
    pub mail_ids: Vec<u32>,
}

#[derive(Debug, Clone)]
pub struct CmGetMailAttachment {
    pub mail_id: u32,
    pub attach_type: u8,
}

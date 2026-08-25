//! Pacotes do Servidor para Correio e Mensagens (SM_MAIL - Padrão Classic 4.5)

#[derive(Debug, Clone)]
pub struct SmMail {
    pub mail_id: u32,
    pub sender_name: String,
    pub title: String,
    pub message: String,
    pub unread: bool,
    pub attached_kinah: u64,
}

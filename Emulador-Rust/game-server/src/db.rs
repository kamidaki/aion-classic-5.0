//! Camada de Banco de Dados e DAOs
//!
//! Todas as implementações concretas de tabelas estão organizadas de forma modular em `crate::dao::`:
//! - `crate::dao::schema`: Criação centralizada e migrações SQLite
//! - `crate::dao::account_dao`: Tabela `account_data`
//! - `crate::dao::session_dao`: Tabela `sessions` e resolução cross-db
//! - `crate::dao::character_dao`: Tabelas `characters`, `players`
//! - `crate::dao::inventory_dao`: Tabela `character_items`
//! - `crate::dao::skill_dao`: Tabela `character_skills`
//! - `crate::dao::quest_dao`: Tabela `player_quests`
//! - `crate::dao::mail_dao`: Tabela `character_mail`
//! - `crate::dao::guild_dao`: Tabelas `guilds`, `guild_members`
//! - `crate::dao::broker_dao`: Tabelas `broker_listings`, `broker_history`
//! - `crate::dao::buddy_dao`: Tabela `character_buddies`

pub use crate::dao::*;

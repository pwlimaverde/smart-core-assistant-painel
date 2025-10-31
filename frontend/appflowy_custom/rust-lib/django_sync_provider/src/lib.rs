//! Provider de sincronização para integração com o Django.
//!
//! Comentários em Português conforme padrão do projeto.

use serde::{Deserialize, Serialize};
use thiserror::Error;

/// Erros de sincronização.
#[derive(Debug, Error)]
pub enum SyncError {
    #[error("network error: {0}")]
    Network(String),
    #[error("serialization error: {0}")]
    Serde(String),
    #[error("unexpected error: {0}")]
    Unexpected(String),
}

/// Representa uma linha do Grid de Atendimentos.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Row {
    pub row_id: String,
    pub ticket_id: String,
    pub name: String,
    pub status: String,
    pub priority: String,
    pub assigned_to: String,
    pub tags: Vec<String>,
    pub last_message: String,
    pub version: i64,
}

/// Patch de atualização/criação para linhas.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RowPatch {
    pub row_id: Option<String>,
    pub ticket_id: String,
    pub name: Option<String>,
    pub status: Option<String>,
    pub priority: Option<String>,
    pub assigned_to: Option<String>,
    pub tags: Option<Vec<String>>,
    pub last_message: Option<String>,
    pub version: Option<i64>,
}

/// Delta de mudanças recebido em `pull_rows`.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RowDelta {
    pub change_type: String, // "created" | "updated" | "deleted"
    pub row: Option<Row>,
    pub row_id: Option<String>,
    pub since: String, // ISO8601
}

/// Contrato de sincronização remoto.
pub trait RemoteSync {
    /// Envia patches de linhas para o adapter Django.
    fn push_rows(&self, grid_id: &str, patches: &[RowPatch])
        -> Result<(), SyncError>;

    /// Obtém deltas de linhas desde um instante `since` (ISO8601).
    fn pull_rows(&self, grid_id: &str, since: &str)
        -> Result<Vec<RowDelta>, SyncError>;

    /// Assina mudanças de um grid (stub inicial).
    fn subscribe(&self, grid_id: &str) -> Result<(), SyncError>;
}

/// Implementação base do provider para o Django.
pub struct DjangoSyncProvider {
    pub base_url: String,
    pub jwt: Option<String>,
}

impl DjangoSyncProvider {
    /// Cria um provider com base URL e token opcional.
    pub fn new<S: Into<String>>(base_url: S, jwt: Option<String>) -> Self {
        Self {
            base_url: base_url.into(),
            jwt,
        }
    }
}

impl RemoteSync for DjangoSyncProvider {
    fn push_rows(&self, _grid_id: &str, _patches: &[RowPatch])
        -> Result<(), SyncError>
    {
        // MVI: implementação futura com `reqwest` + JWT.
        Ok(())
    }

    fn pull_rows(&self, _grid_id: &str, _since: &str)
        -> Result<Vec<RowDelta>, SyncError>
    {
        // MVI: retorna vetor vazio por enquanto.
        Ok(Vec::new())
    }

    fn subscribe(&self, _grid_id: &str) -> Result<(), SyncError> {
        // MVI: stub inicial sem stream.
        Ok(())
    }
}
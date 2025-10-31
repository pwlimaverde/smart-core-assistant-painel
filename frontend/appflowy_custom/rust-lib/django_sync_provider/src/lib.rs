//! Provider de sincronização para integração com o Django.
//!
//! Comentários em Português conforme padrão do projeto.

use serde::{Deserialize, Serialize};
use thiserror::Error;
use reqwest::blocking::Client;
use reqwest::header::{HeaderMap, HeaderValue, AUTHORIZATION, IF_MATCH};
use std::fs;
use std::env;
use std::io::{Read, Write};
use std::path::{Path, PathBuf};
use chrono::{DateTime, Utc};
use directories::ProjectDirs;
use dotenvy::dotenv;

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

/// Payload de criação de linha no servidor.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RowCreate {
    pub ticket_id: String,
    pub name: String,
    pub status: String,
    pub priority: String,
    pub assigned_to: String,
    pub tags: Vec<String>,
    pub last_message: String,
}

/// Tokens de autenticação JWT (SimpleJWT).
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AuthTokens {
    pub access: String,
    pub refresh: String,
}

/// Estado de sincronização persistido por `grid_id`.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SyncState {
    pub last_since: Option<String>,
    pub last_version: Option<i64>,
    pub saved_at: String, // ISO8601
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
    pub refresh_token: Option<String>,
    client: Client,
}

impl DjangoSyncProvider {
    /// Cria um provider com base URL e token opcional.
    pub fn new<S: Into<String>>(base_url: S, jwt: Option<String>) -> Self {
        Self {
            base_url: base_url.into(),
            jwt,
            refresh_token: None,
            client: Client::new(),
        }
    }

    /// Constrói provider lendo `APPFLOWY_ADAPTER_BASE_URL` do ambiente (.env).
    ///
    /// Observação de segurança: credenciais não são carregadas nem persistidas
    /// aqui. Use `login_from_env` para autenticar sem armazenar username/password.
    pub fn from_env() -> Result<Self, SyncError> {
        // Carrega .env se existir; ignora erros.
        dotenv().ok();
        let base_url = env::var("APPFLOWY_ADAPTER_BASE_URL")
            .map_err(|_| SyncError::Unexpected("APPFLOWY_ADAPTER_BASE_URL ausente".into()))?;
        Ok(Self::new(base_url, None))
    }

    /// Efetua login usando `APPFLOWY_ADAPTER_USERNAME`/`APPFLOWY_ADAPTER_PASSWORD` do ambiente.
    /// Não persiste credenciais; tokens (access/refresh) ficam apenas em memória.
    pub fn login_from_env(&mut self) -> Result<(), SyncError> {
        dotenv().ok();
        let username = env::var("APPFLOWY_ADAPTER_USERNAME")
            .map_err(|_| SyncError::Unexpected("APPFLOWY_ADAPTER_USERNAME ausente".into()))?;
        let password = env::var("APPFLOWY_ADAPTER_PASSWORD")
            .map_err(|_| SyncError::Unexpected("APPFLOWY_ADAPTER_PASSWORD ausente".into()))?;
        self.auth_login(&username, &password)
    }

    /// Realiza login JWT e guarda tokens em memória.
    pub fn auth_login(&mut self, username: &str, password: &str) -> Result<(), SyncError> {
        // Observação: nunca persistir credenciais em texto plano.
        let url = format!("{}/auth/login/", self.base_url_trim());
        let body = serde_json::json!({
            "username": username,
            "password": password,
        });
        let resp = self
            .client
            .post(&url)
            .json(&body)
            .send()
            .map_err(|e| SyncError::Network(e.to_string()))?;

        if !resp.status().is_success() {
            return Err(SyncError::Unexpected(format!(
                "login failed: status {}",
                resp.status()
            )));
        }

        let tokens: AuthTokens = resp
            .json()
            .map_err(|e| SyncError::Serde(e.to_string()))?;
        self.jwt = Some(tokens.access);
        self.refresh_token = Some(tokens.refresh);
        Ok(())
    }

    /// Renova o token de acesso usando o refresh token.
    pub fn auth_refresh(&mut self) -> Result<(), SyncError> {
        let refresh = self
            .refresh_token
            .clone()
            .ok_or_else(|| SyncError::Unexpected("missing refresh token".into()))?;
        let url = format!("{}/auth/refresh/", self.base_url_trim());
        let body = serde_json::json!({
            "refresh": refresh,
        });
        let resp = self
            .client
            .post(&url)
            .json(&body)
            .send()
            .map_err(|e| SyncError::Network(e.to_string()))?;

        if !resp.status().is_success() {
            return Err(SyncError::Unexpected(format!(
                "refresh failed: status {}",
                resp.status()
            )));
        }

        // SimpleJWT retorna apenas `access`.
        #[derive(Deserialize)]
        struct RefreshResp { access: String }
        let data: RefreshResp = resp
            .json()
            .map_err(|e| SyncError::Serde(e.to_string()))?;
        self.jwt = Some(data.access);
        Ok(())
    }

    /// Carrega estado de sincronização do disco.
    pub fn load_sync_state(&self, grid_id: &str) -> Result<Option<SyncState>, SyncError> {
        let path = self.sync_state_path(grid_id);
        if !path.exists() { return Ok(None); }
        let mut file = fs::File::open(&path)
            .map_err(|e| SyncError::Unexpected(format!("open state: {}", e)))?;
        let mut buf = String::new();
        file.read_to_string(&mut buf)
            .map_err(|e| SyncError::Unexpected(format!("read state: {}", e)))?;
        let state: SyncState = serde_json::from_str(&buf)
            .map_err(|e| SyncError::Serde(e.to_string()))?;
        Ok(Some(state))
    }

    /// Persiste estado de sincronização no disco.
    pub fn save_sync_state(&self, grid_id: &str, state: &SyncState) -> Result<(), SyncError> {
        let path = self.sync_state_path(grid_id);
        if let Some(parent) = path.parent() {
            fs::create_dir_all(parent)
                .map_err(|e| SyncError::Unexpected(format!("mkdir: {}", e)))?;
        }
        let mut file = fs::File::create(&path)
            .map_err(|e| SyncError::Unexpected(format!("create state: {}", e)))?;
        let data = serde_json::to_string_pretty(state)
            .map_err(|e| SyncError::Serde(e.to_string()))?;
        file.write_all(data.as_bytes())
            .map_err(|e| SyncError::Unexpected(format!("write state: {}", e)))?;
        Ok(())
    }

    /// Caminho do arquivo de estado por grid.
    fn sync_state_path(&self, grid_id: &str) -> PathBuf {
        // Usa diretório de dados do aplicativo no Windows.
        let dirs = ProjectDirs::from("com", "smartcore", "smart_core_assistant");
        let base: PathBuf = if let Some(d) = dirs { d.data_dir().to_path_buf() } else { Path::new(".").to_path_buf() };
        base.join("django_sync_provider").join("sync_state").join(format!("{}.json", grid_id))
    }

    fn base_url_trim(&self) -> String {
        self.base_url.trim_end_matches('/').to_string()
    }

    fn auth_header(&self) -> Option<HeaderValue> {
        self.jwt.as_ref().and_then(|t| {
            let v = format!("Bearer {}", t);
            HeaderValue::from_str(&v).ok()
        })
    }
}

impl RemoteSync for DjangoSyncProvider {
    fn push_rows(&self, grid_id: &str, patches: &[RowPatch]) -> Result<(), SyncError> {
        let base = self.base_url_trim();
        let mut headers = HeaderMap::new();
        if let Some(auth) = self.auth_header() { headers.insert(AUTHORIZATION, auth); }

        for p in patches {
            if let Some(row_id) = &p.row_id {
                // Atualização com If-Match.
                let url = format!("{}/grids/{}/rows/{}/", base, grid_id, row_id);
                let mut req = self.client.put(&url).headers(headers.clone());
                if let Some(v) = p.version { req = req.header(IF_MATCH, v.to_string()); }
                let body = serde_json::to_value(p).map_err(|e| SyncError::Serde(e.to_string()))?;
                let resp = req.json(&body).send().map_err(|e| SyncError::Network(e.to_string()))?;
                if resp.status().as_u16() == 412 {
                    // Conflito: versão divergente (LWW inicial — relatar e seguir).
                    return Err(SyncError::Unexpected("precondition failed (412)".into()));
                }
                if !resp.status().is_success() {
                    return Err(SyncError::Unexpected(format!("update failed: status {}", resp.status())));
                }
            } else {
                // Criação.
                let url = format!("{}/grids/{}/rows/", base, grid_id);
                let create = RowCreate {
                    ticket_id: p.ticket_id.clone(),
                    name: p.name.clone().unwrap_or_else(|| "".to_string()),
                    status: p.status.clone().unwrap_or_else(|| "open".to_string()),
                    priority: p.priority.clone().unwrap_or_else(|| "medium".to_string()),
                    assigned_to: p.assigned_to.clone().unwrap_or_else(|| "".to_string()),
                    tags: p.tags.clone().unwrap_or_default(),
                    last_message: p.last_message.clone().unwrap_or_default(),
                };
                let resp = self
                    .client
                    .post(&url)
                    .headers(headers.clone())
                    .json(&create)
                    .send()
                    .map_err(|e| SyncError::Network(e.to_string()))?;
                if !resp.status().is_success() {
                    return Err(SyncError::Unexpected(format!("create failed: status {}", resp.status())));
                }
            }
        }

        Ok(())
    }

    fn pull_rows(&self, grid_id: &str, since: &str) -> Result<Vec<RowDelta>, SyncError> {
        let base = self.base_url_trim();
        let mut req = self
            .client
            .get(&format!("{}/grids/{}/rows/", base, grid_id))
            .query(&[("since", since)]);
        if let Some(auth) = self.auth_header() { req = req.header(AUTHORIZATION, auth); }
        let resp = req.send().map_err(|e| SyncError::Network(e.to_string()))?;
        if !resp.status().is_success() {
            return Err(SyncError::Unexpected(format!("pull failed: status {}", resp.status())));
        }

        // MVP: servidor retorna lista de linhas; convertemos em deltas "updated".
        let rows: Vec<Row> = resp.json().map_err(|e| SyncError::Serde(e.to_string()))?;
        let deltas = rows
            .into_iter()
            .map(|row| RowDelta {
                change_type: "updated".to_string(),
                row: Some(row),
                row_id: None,
                since: since.to_string(),
            })
            .collect();
        Ok(deltas)
    }

    fn subscribe(&self, _grid_id: &str) -> Result<(), SyncError> {
        // MVI: stub inicial sem stream.
        Ok(())
    }
}
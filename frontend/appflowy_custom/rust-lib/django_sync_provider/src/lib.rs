//! Provider de sincronização para integração com o Django.
//!
//! Comentários em Português conforme padrão do projeto.

use serde::{Deserialize, Serialize};
use thiserror::Error;
use reqwest::blocking::{Client, Response};
use reqwest::header::{HeaderMap, HeaderValue, AUTHORIZATION, IF_MATCH};
use std::fs;
use std::env;
use std::io::{Read, Write};
use std::path::{Path, PathBuf};
use chrono::{DateTime, Utc};
use directories::ProjectDirs;
use dotenvy::dotenv;
use rand::Rng;
use std::thread;
use std::time::Duration;

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
    fn push_rows(&mut self, grid_id: &str, patches: &[RowPatch])
        -> Result<(), SyncError>;

    /// Obtém deltas de linhas desde um instante `since` (ISO8601).
    fn pull_rows(&mut self, grid_id: &str, since: &str)
        -> Result<Vec<RowDelta>, SyncError>;

    /// Assina mudanças de um grid (stub inicial).
    fn subscribe(&mut self, grid_id: &str) -> Result<(), SyncError>;
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

    /// Executa uma requisição com backoff exponencial e jitter.
    ///
    /// - Reintenta automaticamente em erros de rede e status 429/5xx.
    /// - Em 401, tenta `auth_refresh()` e refaz imediatamente.
    ///
    /// `build` deve construir um `RequestBuilder` novo a cada chamada.
    fn execute_with_backoff<F>(&mut self, mut build: F) -> Result<Response, SyncError>
    where
        F: FnMut(&Client) -> reqwest::blocking::RequestBuilder,
    {
        let mut attempt: usize = 0;
        let max_attempts: usize = 5;
        let mut delay_ms: u64 = 150; // base inicial ~150ms
        let max_delay_ms: u64 = 3000; // cap em 3s
        let mut rng = rand::thread_rng();

        loop {
            let resp = build(&self.client).send();
            match resp {
                Ok(r) => {
                    let code = r.status().as_u16();
                    if code == 401 {
                        // Tenta refresh e refaz uma vez por tentativa.
                        if let Err(e) = self.auth_refresh() {
                            return Err(e);
                        }
                        // Pequeno delay para evitar tempestade.
                        let jitter = rng.gen_range(0..=100);
                        thread::sleep(Duration::from_millis(50 + jitter));
                        attempt += 1;
                        if attempt >= max_attempts {
                            return Err(SyncError::Unexpected("401 após refresh".into()));
                        }
                        continue;
                    }

                    if code == 429 || (500..=599).contains(&code) {
                        attempt += 1;
                        if attempt >= max_attempts {
                            return Err(SyncError::Unexpected(format!(
                                "transient status {} após {} tentativas",
                                r.status(), attempt
                            )));
                        }
                        let jitter = rng.gen_range(0..=delay_ms);
                        thread::sleep(Duration::from_millis(delay_ms + jitter));
                        delay_ms = (delay_ms * 2).min(max_delay_ms);
                        continue;
                    }

                    // Retorna mesmo em 4xx para tratamento específico do chamador.
                    return Ok(r);
                }
                Err(e) => {
                    attempt += 1;
                    if attempt >= max_attempts {
                        return Err(SyncError::Network(e.to_string()));
                    }
                    let jitter = rng.gen_range(0..=delay_ms);
                    thread::sleep(Duration::from_millis(delay_ms + jitter));
                    delay_ms = (delay_ms * 2).min(max_delay_ms);
                }
            }
        }
    }
}

impl RemoteSync for DjangoSyncProvider {
    fn push_rows(&mut self, grid_id: &str, patches: &[RowPatch]) -> Result<(), SyncError> {
        let base = self.base_url_trim();
        let mut headers = HeaderMap::new();
        if let Some(auth) = self.auth_header() { headers.insert(AUTHORIZATION, auth); }

        for p in patches {
            if let Some(row_id) = &p.row_id {
                // Atualização com If-Match.
                let url = format!("{}/grids/{}/rows/{}/", base, grid_id, row_id);
                let body = serde_json::to_value(p).map_err(|e| SyncError::Serde(e.to_string()))?;

                // Loop LWW: em 412, usa `current_version` do servidor e refaz.
                let mut attempt_version: Option<i64> = p.version;
                let max_lww_attempts = 3;
                for _ in 0..max_lww_attempts {
                    let build = |client: &Client| {
                        let mut rb = client.put(&url).headers(headers.clone());
                        if let Some(v) = attempt_version { rb = rb.header(IF_MATCH, v.to_string()); }
                        // Clona o body a cada tentativa para não mover
                        let body_clone = body.clone();
                        rb.json(&body_clone)
                    };
                    let resp = self.execute_with_backoff(build)?;
                    let code = resp.status().as_u16();
                    if code == 412 {
                        // Extrai `current_version` e continua (LWW: cliente vence).
                        #[derive(Deserialize)]
                        struct ConflictResp { current_version: i64 }
                        let data: Result<ConflictResp, _> = resp.json();
                        match data {
                            Ok(d) => {
                                attempt_version = Some(d.current_version);
                                continue;
                            }
                            Err(e) => {
                                return Err(SyncError::Serde(format!("falha ao ler 412: {}", e)));
                            }
                        }
                    }

                    if !resp.status().is_success() {
                        return Err(SyncError::Unexpected(format!(
                            "update failed: status {}",
                            resp.status()
                        )));
                    }

                    // Sucesso
                    break;
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
                let build = |client: &Client| {
                    client
                        .post(&url)
                        .headers(headers.clone())
                        .json(&create)
                };
                let resp = self.execute_with_backoff(build)?;
                if !resp.status().is_success() {
                    return Err(SyncError::Unexpected(format!(
                        "create failed: status {}",
                        resp.status()
                    )));
                }
            }
        }

        Ok(())
    }

    fn pull_rows(&mut self, grid_id: &str, since: &str) -> Result<Vec<RowDelta>, SyncError> {
        let base = self.base_url_trim();
        let url = format!("{}/grids/{}/rows/", base, grid_id);
        let build = |client: &Client| {
            let mut rb = client.get(&url).query(&[("since", since)]);
            if let Some(auth) = self.auth_header() { rb = rb.header(AUTHORIZATION, auth); }
            rb
        };
        let resp = self.execute_with_backoff(build)?;
        if !resp.status().is_success() {
            return Err(SyncError::Unexpected(format!(
                "pull failed: status {}",
                resp.status()
            )));
        }

        // Servidor retorna { items: [...] }; convertemos em deltas "updated".
        #[derive(Deserialize)]
        struct RowsList { items: Vec<Row> }
        let list: RowsList = resp.json().map_err(|e| SyncError::Serde(e.to_string()))?;
        let rows = list.items;
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

    fn subscribe(&mut self, _grid_id: &str) -> Result<(), SyncError> {
        // MVI: stub inicial sem stream.
        Ok(())
    }
}

/// Tipos auxiliares para resolução por nome.
#[derive(Debug, Clone, Deserialize)]
pub struct WorkspaceItem { pub workspace_id: String, pub name: String }

#[derive(Debug, Clone, Deserialize)]
pub struct GridItem { pub grid_id: String, pub workspace: String, pub name: String, pub description: Option<String> }

#[derive(Debug, Deserialize)]
struct ListResp<T> { items: Vec<T> }

impl DjangoSyncProvider {
    /// Resolve o `workspace_id` pelo nome quando não definido no `.env`.
    pub fn resolve_workspace_id_by_name(&mut self, name: &str) -> Result<String, SyncError> {
        let base = self.base_url_trim();
        let url = format!("{}/workspaces/", base);
        let build = |client: &Client| {
            let mut rb = client.get(&url);
            if let Some(auth) = self.auth_header() { rb = rb.header(AUTHORIZATION, auth); }
            rb
        };
        let resp = self.execute_with_backoff(build)?;
        if !resp.status().is_success() {
            return Err(SyncError::Unexpected(format!("workspaces failed: {}", resp.status())));
        }
        let list: ListResp<WorkspaceItem> = resp.json().map_err(|e| SyncError::Serde(e.to_string()))?;
        let found = list.items.into_iter().find(|w| w.name == name)
            .ok_or_else(|| SyncError::Unexpected("workspace não encontrado por nome".into()))?;
        Ok(found.workspace_id)
    }

    /// Resolve o `grid_id` pelo nome dentro de um workspace.
    /// Requer o endpoint Django `GET /workspaces/{workspace_id}/grids/`.
    pub fn resolve_grid_id_by_name(&mut self, workspace_id: &str, name: &str) -> Result<String, SyncError> {
        let base = self.base_url_trim();
        let url = format!("{}/workspaces/{}/grids/", base, workspace_id);
        let build = |client: &Client| {
            let mut rb = client.get(&url);
            if let Some(auth) = self.auth_header() { rb = rb.header(AUTHORIZATION, auth); }
            rb
        };
        let resp = self.execute_with_backoff(build)?;
        if !resp.status().is_success() {
            return Err(SyncError::Unexpected(format!("grids list failed: {}", resp.status())));
        }
        let list: ListResp<GridItem> = resp.json().map_err(|e| SyncError::Serde(e.to_string()))?;
        let found = list.items.into_iter().find(|g| g.name == name)
            .ok_or_else(|| SyncError::Unexpected("grid não encontrado por nome".into()))?;
        Ok(found.grid_id)
    }
}
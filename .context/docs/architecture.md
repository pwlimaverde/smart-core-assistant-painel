---
status: unfilled
generated: 2026-01-15
---

# Architecture Notes

Describe how the system is assembled and why the current design exists.

## System Architecture Overview

Summarize the top-level topology (monolith, modular service, microservices) and deployment model. Highlight how requests traverse the system and where control pivots between layers.

## Architectural Layers
### Services
Business logic and orchestration
- **Directories**: `teste_debug`, `tests\modules\services`, `tests\modules\services\features`, `src\smart_core_assistant_painel\modules\services`, `src\smart_core_assistant_painel\modules\services\utils`, `src\smart_core_assistant_painel\modules\services\features`, `src\smart_core_assistant_painel\modules\services\config`, `src\smart_core_assistant_painel\app\ui\treinamento`, `src\smart_core_assistant_painel\app\trello_sync\services`, `src\smart_core_assistant_painel\app\tenants\services`, `src\smart_core_assistant_painel\app\evolution_sync\services`, `tests\modules\services\features\unifield_data_services\datasource`, `tests\modules\services\features\set_environ_remote\datasource`, `src\smart_core_assistant_painel\modules\services\features\unifield_data_services`, `src\smart_core_assistant_painel\app\ui\atendimentos\services`, `src\smart_core_assistant_painel\app\evolution_sync\tests\services`, `tests\modules\services\features\unifield_data_services\domain\usecase`, `tests\modules\services\features\set_environ_remote\domain\usecase`, `tests\modules\initial_loading\features\firebase_init\domain\usecase`, `tests\modules\ai_engine\features\load_document_file\domain\usecase`, `tests\modules\ai_engine\features\analise_previa_mensagem\domain\usecase`, `tests\modules\ai_engine\features\load_mensage_data\domain\usecase`, `tests\modules\ai_engine\features\load_document_conteudo\domain\usecase`, `tests\modules\ai_engine\features\analise_conteudo\domain\usecase`, `src\smart_core_assistant_painel\modules\services\features\unifield_data_services\domain`, `src\smart_core_assistant_painel\modules\services\features\unifield_data_services\datasource`, `src\smart_core_assistant_painel\app\ui\atendimentos\tests\services`, `src\smart_core_assistant_painel\modules\initial_loading\features\firebase_init\domain\usecase`, `src\smart_core_assistant_painel\modules\ai_engine\features\load_document_file\domain\usecase`, `src\smart_core_assistant_painel\modules\ai_engine\features\load_mensage_data\domain\usecase`, `src\smart_core_assistant_painel\modules\ai_engine\features\generate_chunks\domain\usecase`, `src\smart_core_assistant_painel\modules\ai_engine\features\load_document_conteudo\domain\usecase`, `src\smart_core_assistant_painel\modules\ai_engine\features\analise_previa_mensagem\domain\usecase`, `src\smart_core_assistant_painel\modules\ai_engine\features\generate_embeddings\domain\usecase`, `src\smart_core_assistant_painel\modules\ai_engine\features\analise_mensage\domain\usecase`, `src\smart_core_assistant_painel\modules\ai_engine\features\analise_conteudo\domain\usecase`, `src\smart_core_assistant_painel\modules\ai_engine\features\analise_avaliacao\domain\usecase`, `src\smart_core_assistant_painel\modules\services\features\unifield_data_services\domain\usecase`, `src\smart_core_assistant_painel\modules\services\features\unifield_data_services\domain\interface`
- **Symbols**: 91 total, 90 exported
- **Key exports**:
  - [`verify_service_hub`](teste_debug\verify_service_hub.py#L23) (function)
  - [`TestStartServices`](tests\modules\services\test_start_services.py#L18) (class)
  - [`TestServiceHub`](tests\modules\services\features\test_service_hub.py#L8) (class)
  - [`start_services`](src\smart_core_assistant_painel\modules\services\start_services.py#L78) (function)
  - [`SetEnvironRemoteParameters`](src\smart_core_assistant_painel\modules\services\utils\parameters.py#L19) (class)
  - [`UnifieldDataServicesParameters`](src\smart_core_assistant_painel\modules\services\utils\parameters.py#L39) (class)
  - [`SetEnvironRemoteError`](src\smart_core_assistant_painel\modules\services\utils\erros.py#L14) (class)
  - [`UnifieldDataServicesError`](src\smart_core_assistant_painel\modules\services\utils\erros.py#L25) (class)
  - [`ServiceHub`](src\smart_core_assistant_painel\modules\services\features\service_hub.py#L19) (class)
  - [`FeaturesCompose`](src\smart_core_assistant_painel\modules\services\features\features_compose.py#L27) (class)
  - [`ConfigProvider`](src\smart_core_assistant_painel\modules\services\config\provider.py#L4) (class)
  - [`RuntimeConfig`](src\smart_core_assistant_painel\modules\services\config\context.py#L7) (class)
  - [`set_config`](src\smart_core_assistant_painel\modules\services\config\context.py#L68) (function)
  - [`get_config`](src\smart_core_assistant_painel\modules\services\config\context.py#L73) (function)
  - [`get_config_or_default`](src\smart_core_assistant_painel\modules\services\config\context.py#L88) (function)
  - [`TreinamentoService`](src\smart_core_assistant_painel\app\ui\treinamento\services.py#L13) (class)
  - [`WebhookProcessingService`](src\smart_core_assistant_painel\app\trello_sync\services\webhook_processing_service.py#L8) (class)
  - [`TicketSyncService`](src\smart_core_assistant_painel\app\trello_sync\services\ticket_sync_service.py#L34) (class)
  - [`MemberSyncService`](src\smart_core_assistant_painel\app\trello_sync\services\member_sync_service.py#L25) (class)
  - [`FlowSyncService`](src\smart_core_assistant_painel\app\trello_sync\services\flow_sync_service.py#L24) (class)
  - [`TenantProvisioningService`](src\smart_core_assistant_painel\app\tenants\services\provisioning.py#L9) (class)
  - [`ConnectionTester`](src\smart_core_assistant_painel\app\tenants\services\connection_tester.py#L16) (class)
  - [`TenantMigrationRunner`](src\smart_core_assistant_painel\app\tenants\services\connection_tester.py#L135) (class)
  - [`ConfigLoader`](src\smart_core_assistant_painel\app\tenants\services\config_loader.py#L15) (class)
  - [`WebhookProcessor`](src\smart_core_assistant_painel\app\evolution_sync\services\webhook.py#L27) (class)
  - [`set_buffer_contact`](src\smart_core_assistant_painel\app\evolution_sync\services\message_buffer.py#L15) (function)
  - [`get_and_clear_buffer_contact`](src\smart_core_assistant_painel\app\evolution_sync\services\message_buffer.py#L36) (function)
  - [`clear_scheduling_lock`](src\smart_core_assistant_painel\app\evolution_sync\services\message_buffer.py#L49) (function)
  - [`clear_buffer_contact`](src\smart_core_assistant_painel\app\evolution_sync\services\message_buffer.py#L57) (function)
  - [`sched_response_contact`](src\smart_core_assistant_painel\app\evolution_sync\services\message_buffer.py#L64) (function)
  - [`EvolutionWhatsAppService`](src\smart_core_assistant_painel\app\evolution_sync\services\evolution_api.py#L7) (class)
  - [`TestUnifieldDataServicesDatasource`](tests\modules\services\features\unifield_data_services\datasource\test_unifield_data_services_datasource.py#L23) (class)
  - [`TestInMemoryUnifiedDataService`](tests\modules\services\features\unifield_data_services\datasource\test_unifield_data_services_datasource.py#L65) (class)
  - [`TestTrelloUnifiedDataService`](tests\modules\services\features\unifield_data_services\datasource\test_trello_adapter.py#L16) (class)
  - [`TestClicupUnifiedDataService`](tests\modules\services\features\unifield_data_services\datasource\test_clicup_adapter.py#L16) (class)
  - [`mock_firebase_admin`](tests\modules\services\features\set_environ_remote\datasource\test_set_environ_remote_firebase_datasource.py#L19) (function)
  - [`mock_remote_config`](tests\modules\services\features\set_environ_remote\datasource\test_set_environ_remote_firebase_datasource.py#L24) (function)
  - [`TestSetEnvironRemoteFirebaseDatasource`](tests\modules\services\features\set_environ_remote\datasource\test_set_environ_remote_firebase_datasource.py#L35) (class)
  - [`create_orchestrator`](src\smart_core_assistant_painel\app\ui\atendimentos\services\__init__.py#L38) (function)
  - [`MessageAnalyzer`](src\smart_core_assistant_painel\app\ui\atendimentos\services\message_analyzer.py#L24) (class)
  - [`MessageAnalyzerInterface`](src\smart_core_assistant_painel\app\ui\atendimentos\services\interfaces.py#L22) (class)
  - [`AttendanceStructureManagerInterface`](src\smart_core_assistant_painel\app\ui\atendimentos\services\interfaces.py#L56) (class)
  - [`BotRulesEngineInterface`](src\smart_core_assistant_painel\app\ui\atendimentos\services\interfaces.py#L96) (class)
  - [`AttendanceOrchestratorInterface`](src\smart_core_assistant_painel\app\ui\atendimentos\services\interfaces.py#L126) (class)
  - [`BotRulesEngine`](src\smart_core_assistant_painel\app\ui\atendimentos\services\bot_rules_engine.py#L19) (class)
  - [`AttendanceStructureManager`](src\smart_core_assistant_painel\app\ui\atendimentos\services\attendance_structure_manager.py#L23) (class)
  - [`AttendanceOrchestrator`](src\smart_core_assistant_painel\app\ui\atendimentos\services\attendance_orchestrator.py#L34) (class)
  - [`processor`](src\smart_core_assistant_painel\app\evolution_sync\tests\services\test_webhook.py#L17) (function)
  - [`mock_envelope`](src\smart_core_assistant_painel\app\evolution_sync\tests\services\test_webhook.py#L22) (function)
  - [`test_process_webhook_success`](src\smart_core_assistant_painel\app\evolution_sync\tests\services\test_webhook.py#L47) (function)
  - [`test_process_webhook_ignored_from_me`](src\smart_core_assistant_painel\app\evolution_sync\tests\services\test_webhook.py#L98) (function)
  - [`test_process_webhook_filters_group_messages`](src\smart_core_assistant_painel\app\evolution_sync\tests\services\test_webhook.py#L109) (function)
  - [`service`](src\smart_core_assistant_painel\app\evolution_sync\tests\services\test_evolution_api.py#L12) (function)
  - [`test_send_request_success`](src\smart_core_assistant_painel\app\evolution_sync\tests\services\test_evolution_api.py#L17) (function)
  - [`test_send_message_success`](src\smart_core_assistant_painel\app\evolution_sync\tests\services\test_evolution_api.py#L41) (function)
  - [`test_send_message_failure`](src\smart_core_assistant_painel\app\evolution_sync\tests\services\test_evolution_api.py#L81) (function)
  - [`TestUnifieldDataServicesUseCase`](tests\modules\services\features\unifield_data_services\domain\usecase\test_unifield_data_services_usecase.py#L21) (class)
  - [`TestSetEnvironRemoteUseCase`](tests\modules\services\features\set_environ_remote\domain\usecase\test_set_environ_remote_usecase.py#L18) (class)
  - [`TestFirebaseInitUseCase`](tests\modules\initial_loading\features\firebase_init\domain\usecase\test_firebase_init_usecase.py#L18) (class)
  - [`TestLoadDocumentFileUseCase`](tests\modules\ai_engine\features\load_document_file\domain\usecase\test_load_document_file_usecase.py#L20) (class)
  - [`TestAnalisePreviaMensagemUsecase`](tests\modules\ai_engine\features\analise_previa_mensagem\domain\usecase\test_analise_previa_mensagem_usecase.py#L23) (class)
  - [`TestLoadMensageDataUseCase`](tests\modules\ai_engine\features\load_mensage_data\domain\usecase\test_load_mensage_data_usecase.py#L15) (class)
  - [`TestLoadDocumentConteudoUseCase`](tests\modules\ai_engine\features\load_document_conteudo\domain\usecase\test_load_document_conteudo_usecase.py#L20) (class)
  - [`TestAnaliseConteudoUseCase`](tests\modules\ai_engine\features\analise_conteudo\domain\usecase\test_analise_conteudo_usecase.py#L18) (class)
  - [`UnifieldDataServicesDatasource`](src\smart_core_assistant_painel\modules\services\features\unifield_data_services\datasource\unifield_data_services_datasource.py#L187) (class)
  - [`TrelloUnifiedDataService`](src\smart_core_assistant_painel\modules\services\features\unifield_data_services\datasource\trello_adapter.py#L24) (class)
  - [`NotionUnifiedDataService`](src\smart_core_assistant_painel\modules\services\features\unifield_data_services\datasource\notion_adapter.py#L30) (class)
  - [`ClicupUnifiedDataService`](src\smart_core_assistant_painel\modules\services\features\unifield_data_services\datasource\clicup_adapter.py#L25) (class)
  - [`mock_message`](src\smart_core_assistant_painel\app\ui\atendimentos\tests\services\test_message_analyzer.py#L20) (function)
  - [`TestMessageAnalyzer`](src\smart_core_assistant_painel\app\ui\atendimentos\tests\services\test_message_analyzer.py#L56) (class)
  - [`TestBotRulesEngineFlag`](src\smart_core_assistant_painel\app\ui\atendimentos\tests\services\test_bot_rules_engine_flag.py#L20) (class)
  - [`mock_atendimento`](src\smart_core_assistant_painel\app\ui\atendimentos\tests\services\test_bot_rules_engine.py#L23) (function)
  - [`TestBotRulesEngine`](src\smart_core_assistant_painel\app\ui\atendimentos\tests\services\test_bot_rules_engine.py#L37) (class)
  - [`mock_atendimento_instance`](src\smart_core_assistant_painel\app\ui\atendimentos\tests\services\test_attendance_structure_manager.py#L24) (function)
  - [`TestAttendanceStructureManager`](src\smart_core_assistant_painel\app\ui\atendimentos\tests\services\test_attendance_structure_manager.py#L38) (class)
  - [`mock_services`](src\smart_core_assistant_painel\app\ui\atendimentos\tests\services\test_attendance_orchestrator.py#L19) (function)
  - [`orchestrator_instance`](src\smart_core_assistant_painel\app\ui\atendimentos\tests\services\test_attendance_orchestrator.py#L29) (function)
  - [`TestAttendanceOrchestrator`](src\smart_core_assistant_painel\app\ui\atendimentos\tests\services\test_attendance_orchestrator.py#L40) (class)
  - [`FirebaseInitUseCase`](src\smart_core_assistant_painel\modules\initial_loading\features\firebase_init\domain\usecase\firebase_init_usecase.py#L19) (class)
  - [`LoadDocumentFileUseCase`](src\smart_core_assistant_painel\modules\ai_engine\features\load_document_file\domain\usecase\load_document_file_usecase.py#L18) (class)
  - [`LoadMensageDataUseCase`](src\smart_core_assistant_painel\modules\ai_engine\features\load_mensage_data\domain\usecase\load_mensage_data_usecase.py#L21) (class)
  - [`GenerateChunksUseCase`](src\smart_core_assistant_painel\modules\ai_engine\features\generate_chunks\domain\usecase\generate_chunks_usecase.py#L22) (class)
  - [`LoadDocumentConteudoUseCase`](src\smart_core_assistant_painel\modules\ai_engine\features\load_document_conteudo\domain\usecase\load_document_conteudo_usecase.py#L18) (class)
  - [`AnalisePreviaMensagemUsecase`](src\smart_core_assistant_painel\modules\ai_engine\features\analise_previa_mensagem\domain\usecase\analise_previa_mensagem_usecase.py#L16) (class)
  - [`GenerateEmbeddingsUseCase`](src\smart_core_assistant_painel\modules\ai_engine\features\generate_embeddings\domain\usecase\generate_embeddings_usecase.py#L11) (class)
  - [`AnaliseMensageUseCase`](src\smart_core_assistant_painel\modules\ai_engine\features\analise_mensage\domain\usecase\analise_mensage_usecase.py#L13) (class)
  - [`AnaliseConteudoUseCase`](src\smart_core_assistant_painel\modules\ai_engine\features\analise_conteudo\domain\usecase\analise_conteudo_usecase.py#L11) (class)
  - [`AnaliseAvaliacaoUsecase`](src\smart_core_assistant_painel\modules\ai_engine\features\analise_avaliacao\domain\usecase\analise_avaliacao_usecase.py#L18) (class)
  - [`UnifieldDataServicesUseCase`](src\smart_core_assistant_painel\modules\services\features\unifield_data_services\domain\usecase\unifield_data_services_usecase.py#L16) (class)
  - [`UnifiedDataService`](src\smart_core_assistant_painel\modules\services\features\unifield_data_services\domain\interface\unified_data_service.py#L14) (class)

### Repositories
Data access and persistence
- **Directories**: `teste_debug`, `scripts\temp`, `scripts\temp\database_reset`, `tests\modules\ai_engine\features\load_document_file\datasource`, `tests\modules\ai_engine\features\analise_previa_mensagem\datasource`, `tests\modules\ai_engine\features\generate_embeddings\datasource`, `tests\modules\ai_engine\features\analise_conteudo\datasource`, `src\smart_core_assistant_painel\modules\ai_engine\features\load_mensage_data`, `tests\modules\ai_engine\features\analise_previa_mensagem\datasource\langchain_pydantic`, `tests\modules\ai_engine\features\analise_previa_mensagem\datasource\analise_previa_langchain`, `src\smart_core_assistant_painel\modules\ai_engine\features\load_document_file\datasource`, `src\smart_core_assistant_painel\modules\ai_engine\features\analise_previa_mensagem\datasource`, `src\smart_core_assistant_painel\modules\ai_engine\features\generate_embeddings\datasource`, `src\smart_core_assistant_painel\modules\ai_engine\features\analise_mensage\datasource`, `src\smart_core_assistant_painel\modules\ai_engine\features\analise_conteudo\datasource`, `src\smart_core_assistant_painel\modules\ai_engine\features\analise_avaliacao\datasource`, `src\smart_core_assistant_painel\app\ui\usuarios\management\commands`, `src\smart_core_assistant_painel\modules\ai_engine\features\analise_previa_mensagem\datasource\langchain_pydantic`, `src\smart_core_assistant_painel\modules\ai_engine\features\analise_previa_mensagem\datasource\analise_previa_langchain`
- **Symbols**: 25 total, 25 exported
- **Key exports**:
  - [`test_evolution_metadata_optimization`](teste_debug\verify_evolution_metadata.py#L36) (function)
  - [`print_header`](scripts\temp\loaddata_remoto.py#L20) (function)
  - [`load_env_file`](scripts\temp\loaddata_remoto.py#L28) (function)
  - [`setup_environment`](scripts\temp\loaddata_remoto.py#L48) (function)
  - [`test_connectivity`](scripts\temp\loaddata_remoto.py#L83) (function)
  - [`build_fixture_paths`](scripts\temp\loaddata_remoto.py#L113) (function)
  - [`run_loaddata`](scripts\temp\loaddata_remoto.py#L124) (function)
  - [`show_counts`](scripts\temp\loaddata_remoto.py#L185) (function)
  - [`main`](scripts\temp\loaddata_remoto.py#L225) (function)
  - [`run_command`](scripts\temp\database_reset\reset_database.py#L18) (function)
  - [`main`](scripts\temp\database_reset\reset_database.py#L38) (function)
  - [`TestLoadDocumentFileDatasource`](tests\modules\ai_engine\features\load_document_file\datasource\test_load_document_file_datasource.py#L19) (class)
  - [`TestGenerateEmbeddingsLangchainDatasource`](tests\modules\ai_engine\features\generate_embeddings\datasource\test_generate_embeddings_langchain_datasource.py#L17) (class)
  - [`TestAnaliseConteudoLangchainDatasource`](tests\modules\ai_engine\features\analise_conteudo\datasource\test_analise_conteudo_langchain_datasource.py#L16) (class)
  - [`TestAnalisePreviaMensagemLangchainDatasource`](tests\modules\ai_engine\features\analise_previa_mensagem\datasource\langchain_pydantic\test_analise_previa_mensagem_langchain_datasource.py#L18) (class)
  - [`TestAnalisePreviaMensagemLangchain`](tests\modules\ai_engine\features\analise_previa_mensagem\datasource\langchain_pydantic\test_analise_previa_mensagem_langchain.py#L12) (class)
  - [`TestAnalisePreviaLangchainDatasource`](tests\modules\ai_engine\features\analise_previa_mensagem\datasource\analise_previa_langchain\test_analise_previa_langchain_datasource.py#L20) (class)
  - [`LoadDocumentFileDatasource`](src\smart_core_assistant_painel\modules\ai_engine\features\load_document_file\datasource\load_document_file_datasource.py#L17) (class)
  - [`GenerateEmbeddingsLangchainDatasource`](src\smart_core_assistant_painel\modules\ai_engine\features\generate_embeddings\datasource\generate_embeddings_langchain_datasource.py#L18) (class)
  - [`AnaliseMensageDatasource`](src\smart_core_assistant_painel\modules\ai_engine\features\analise_mensage\datasource\analise_mensage_datasource.py#L19) (class)
  - [`AnaliseConteudoLangchainDatasource`](src\smart_core_assistant_painel\modules\ai_engine\features\analise_conteudo\datasource\analise_conteudo_langchain_datasource.py#L13) (class)
  - [`AnaliseAvaliacaoDatasource`](src\smart_core_assistant_painel\modules\ai_engine\features\analise_avaliacao\datasource\analise_avaliacao_datasource.py#L30) (class)
  - [`Command`](src\smart_core_assistant_painel\app\ui\usuarios\management\commands\seed_dev_data.py#L24) (class)
  - [`AnalisePreviaMensagemLangchain`](src\smart_core_assistant_painel\modules\ai_engine\features\analise_previa_mensagem\datasource\analise_previa_langchain\analise_previa_mensagem_langchain.py#L17) (class)
  - [`AnalisePreviaLangchainDatasource`](src\smart_core_assistant_painel\modules\ai_engine\features\analise_previa_mensagem\datasource\analise_previa_langchain\analise_previa_langchain_datasource.py#L27) (class)

### Config
Configuration and constants
- **Directories**: `scripts\config_global`, `scripts\temp`, `src\smart_core_assistant_painel\app\settings_manager`, `src\smart_core_assistant_painel\app\ui\core`, `src\smart_core_assistant_painel\app\tenants\migrations`, `src\smart_core_assistant_painel\app\settings_manager\migrations`, `src\smart_core_assistant_painel\app\settings_manager\management`, `src\smart_core_assistant_painel\app\settings_manager\management\commands`
- **Symbols**: 25 total, 23 exported
- **Key exports**:
  - [`load_env`](scripts\config_global\sync_coresettings.py#L27) (function)
  - [`escape_sql`](scripts\config_global\sync_coresettings.py#L43) (function)
  - [`run_ssh_psql`](scripts\config_global\sync_coresettings.py#L50) (function)
  - [`dump_action`](scripts\config_global\sync_coresettings.py#L71) (function)
  - [`restore_action`](scripts\config_global\sync_coresettings.py#L106) (function)
  - [`main`](scripts\config_global\sync_coresettings.py#L157) (function)
  - [`load_remote_config`](scripts\temp\extrair_prompts_remote_config.py#L64) (function)
  - [`extract_prompts`](scripts\temp\extrair_prompts_remote_config.py#L79) (function)
  - [`categorize_prompts`](scripts\temp\extrair_prompts_remote_config.py#L91) (function)
  - [`main`](scripts\temp\extrair_prompts_remote_config.py#L143) (function)
  - [`get_core_settings`](scripts\temp\diagnostico_config.py#L201) (function)
  - [`get_runtime_config_fields`](scripts\temp\diagnostico_config.py#L216) (function)
  - [`diagnose`](scripts\temp\diagnostico_config.py#L226) (function)
  - [`print_diagnosis`](scripts\temp\diagnostico_config.py#L282) (function)
  - [`fix_missing_core_settings`](scripts\temp\diagnostico_config.py#L353) (function)
  - [`main`](scripts\temp\diagnostico_config.py#L394) (function)
  - [`SettingsManagerConfig`](src\smart_core_assistant_painel\app\settings_manager\apps.py#L4) (class)
  - [`CoreSettingsAdmin`](src\smart_core_assistant_painel\app\settings_manager\admin.py#L6) (class)
  - [`Migration`](src\smart_core_assistant_painel\app\tenants\migrations\0002_tenant_onboarding_step_tenantconfig_brand_name_and_more.py#L6) (class)
  - [`Migration`](src\smart_core_assistant_painel\app\settings_manager\migrations\0001_initial.py#L6) (class)
  - [`Command`](src\smart_core_assistant_painel\app\settings_manager\management\commands\load_core_settings.py#L17) (class)
  - [`Command`](src\smart_core_assistant_painel\app\settings_manager\management\commands\import_core_settings.py#L15) (class)
  - [`Command`](src\smart_core_assistant_painel\app\settings_manager\management\commands\export_core_settings.py#L13) (class)

### Controllers
Request handling and routing
- **Directories**: `src\smart_core_assistant_painel\app\trello_sync`, `src\smart_core_assistant_painel\app\tenants`, `src\smart_core_assistant_painel\app\ui\operacional`, `src\smart_core_assistant_painel\app\trello_sync\tests`
- **Symbols**: 9 total, 9 exported
- **Key exports**:
  - [`webhook`](src\smart_core_assistant_painel\app\trello_sync\views_api.py#L22) (function)
  - [`TenantDatabaseRouter`](src\smart_core_assistant_painel\app\tenants\db_router.py#L31) (class)
  - [`tenant_required`](src\smart_core_assistant_painel\app\tenants\api_mixins.py#L10) (function)
  - [`TenantQuerysetMixin`](src\smart_core_assistant_painel\app\tenants\api_mixins.py#L22) (class)
  - [`TenantCreateMixin`](src\smart_core_assistant_painel\app\tenants\api_mixins.py#L54) (class)
  - [`TenantForeignKeyValidator`](src\smart_core_assistant_painel\app\tenants\api_mixins.py#L65) (class)
  - [`departamentos_public`](src\smart_core_assistant_painel\app\ui\operacional\views_api.py#L25) (function)
  - [`fluxo_departamento_public`](src\smart_core_assistant_painel\app\ui\operacional\views_api.py#L34) (function)
  - [`WebhookApiTests`](src\smart_core_assistant_painel\app\trello_sync\tests\test_api_public.py#L8) (class)

### Models
Data structures and domain objects
- **Directories**: `src\smart_core_assistant_painel\app\trello_sync`, `src\smart_core_assistant_painel\app\tenants`, `src\smart_core_assistant_painel\app\evolution_sync`, `src\smart_core_assistant_painel\app\settings_manager`, `src\smart_core_assistant_painel\app\ui\usuarios`, `src\smart_core_assistant_painel\app\ui\treinamento`, `src\smart_core_assistant_painel\app\ui\operacional`, `src\smart_core_assistant_painel\app\ui\atendimentos`, `src\smart_core_assistant_painel\app\ui\clientes`, `src\smart_core_assistant_painel\app\trello_sync\tests`, `src\smart_core_assistant_painel\app\evolution_sync\domain`, `tests\modules\initial_loading\features\firebase_init\domain`, `tests\modules\ai_engine\features\load_document_file\domain`, `tests\modules\ai_engine\features\analise_previa_mensagem\domain`, `tests\modules\ai_engine\features\load_document_conteudo\domain`, `tests\modules\ai_engine\features\analise_conteudo\domain`, `src\smart_core_assistant_painel\app\ui\treinamento\tests`, `src\smart_core_assistant_painel\app\ui\atendimentos\tests`, `src\smart_core_assistant_painel\app\ui\clientes\tests`, `src\smart_core_assistant_painel\app\evolution_sync\tests\domain`, `tests\modules\ai_engine\features\analise_previa_mensagem\datasource\langchain_pydantic`, `src\smart_core_assistant_painel\modules\initial_loading\features\firebase_init\domain`, `src\smart_core_assistant_painel\modules\ai_engine\features\load_document_file\domain`, `src\smart_core_assistant_painel\modules\ai_engine\features\load_mensage_data\domain`, `src\smart_core_assistant_painel\modules\ai_engine\features\generate_chunks\domain`, `src\smart_core_assistant_painel\modules\ai_engine\features\load_document_conteudo\domain`, `src\smart_core_assistant_painel\modules\ai_engine\features\analise_previa_mensagem\domain`, `src\smart_core_assistant_painel\modules\ai_engine\features\generate_embeddings\domain`, `src\smart_core_assistant_painel\modules\ai_engine\features\analise_mensage\domain`, `src\smart_core_assistant_painel\modules\ai_engine\features\analise_conteudo\domain`, `src\smart_core_assistant_painel\modules\ai_engine\features\load_mensage_data\domain\model`, `src\smart_core_assistant_painel\modules\ai_engine\features\analise_previa_mensagem\datasource\analise_previa_langchain`, `src\smart_core_assistant_painel\modules\ai_engine\features\analise_previa_mensagem\domain\interface`
- **Symbols**: 97 total, 92 exported
- **Key exports**:
  - [`TrelloBoard`](src\smart_core_assistant_painel\app\trello_sync\models.py#L7) (class)
  - [`TrelloList`](src\smart_core_assistant_painel\app\trello_sync\models.py#L47) (class)
  - [`TrelloMember`](src\smart_core_assistant_painel\app\trello_sync\models.py#L84) (class)
  - [`TrelloCard`](src\smart_core_assistant_painel\app\trello_sync\models.py#L125) (class)
  - [`TrelloWebhookEvent`](src\smart_core_assistant_painel\app\trello_sync\models.py#L168) (class)
  - [`Tenant`](src\smart_core_assistant_painel\app\tenants\models.py#L14) (class)
  - [`TenantDatabase`](src\smart_core_assistant_painel\app\tenants\models.py#L47) (class)
  - [`TenantEvolution`](src\smart_core_assistant_painel\app\tenants\models.py#L85) (class)
  - [`TenantTrello`](src\smart_core_assistant_painel\app\tenants\models.py#L111) (class)
  - [`TenantConfig`](src\smart_core_assistant_painel\app\tenants\models.py#L161) (class)
  - [`Plan`](src\smart_core_assistant_painel\app\tenants\models.py#L311) (class)
  - [`Subscription`](src\smart_core_assistant_painel\app\tenants\models.py#L336) (class)
  - [`PaymentRecord`](src\smart_core_assistant_painel\app\tenants\models.py#L405) (class)
  - [`TenantInvite`](src\smart_core_assistant_painel\app\tenants\models.py#L440) (class)
  - [`TenantUser`](src\smart_core_assistant_painel\app\tenants\models.py#L493) (class)
  - [`EvolutionInstance`](src\smart_core_assistant_painel\app\evolution_sync\models.py#L7) (class)
  - [`EvolutionContact`](src\smart_core_assistant_painel\app\evolution_sync\models.py#L57) (class)
  - [`WhiteList`](src\smart_core_assistant_painel\app\evolution_sync\models.py#L123) (class)
  - [`CoreSettings`](src\smart_core_assistant_painel\app\settings_manager\models.py#L8) (class)
  - [`validate_identificador`](src\smart_core_assistant_painel\app\ui\treinamento\models.py#L17) (function)
  - [`Treinamento`](src\smart_core_assistant_painel\app\ui\treinamento\models.py#L35) (class)
  - [`Documento`](src\smart_core_assistant_painel\app\ui\treinamento\models.py#L106) (class)
  - [`QueryCompose`](src\smart_core_assistant_painel\app\ui\treinamento\models.py#L246) (class)
  - [`validate_telefone`](src\smart_core_assistant_painel\app\ui\operacional\models.py#L20) (function)
  - [`validate_api_key`](src\smart_core_assistant_painel\app\ui\operacional\models.py#L33) (function)
  - [`validate_telefone_instancia`](src\smart_core_assistant_painel\app\ui\operacional\models.py#L43) (function)
  - [`Departamento`](src\smart_core_assistant_painel\app\ui\operacional\models.py#L54) (class)
  - [`Atendente`](src\smart_core_assistant_painel\app\ui\operacional\models.py#L210) (class)
  - [`AppInstance`](src\smart_core_assistant_painel\app\ui\operacional\models.py#L432) (class)
  - [`TipoEtapa`](src\smart_core_assistant_painel\app\ui\operacional\models.py#L486) (class)
  - [`FluxoAtendimento`](src\smart_core_assistant_painel\app\ui\operacional\models.py#L495) (class)
  - [`EtapaFluxo`](src\smart_core_assistant_painel\app\ui\operacional\models.py#L559) (class)
  - [`StatusAtendimento`](src\smart_core_assistant_painel\app\ui\atendimentos\models.py#L24) (class)
  - [`TipoMensagem`](src\smart_core_assistant_painel\app\ui\atendimentos\models.py#L39) (class)
  - [`TipoRemetente`](src\smart_core_assistant_painel\app\ui\atendimentos\models.py#L82) (class)
  - [`Atendimento`](src\smart_core_assistant_painel\app\ui\atendimentos\models.py#L88) (class)
  - [`Mensagem`](src\smart_core_assistant_painel\app\ui\atendimentos\models.py#L996) (class)
  - [`MovimentoFluxo`](src\smart_core_assistant_painel\app\ui\atendimentos\models.py#L1122) (class)
  - [`inicializar_atendimento_whatsapp`](src\smart_core_assistant_painel\app\ui\atendimentos\models.py#L1253) (function)
  - [`buscar_atendimento_ativo`](src\smart_core_assistant_painel\app\ui\atendimentos\models.py#L1333) (function)
  - [`processar_mensagem_whatsapp`](src\smart_core_assistant_painel\app\ui\atendimentos\models.py#L1363) (function)
  - [`buscar_atendimento_ativo_por_contato`](src\smart_core_assistant_painel\app\ui\atendimentos\models.py#L1419) (function)
  - [`inicializar_atendimento_por_contato`](src\smart_core_assistant_painel\app\ui\atendimentos\models.py#L1439) (function)
  - [`processar_mensagem_por_contato`](src\smart_core_assistant_painel\app\ui\atendimentos\models.py#L1571) (function)
  - [`validate_telefone`](src\smart_core_assistant_painel\app\ui\clientes\models.py#L9) (function)
  - [`validate_cnpj`](src\smart_core_assistant_painel\app\ui\clientes\models.py#L22) (function)
  - [`validate_cpf`](src\smart_core_assistant_painel\app\ui\clientes\models.py#L37) (function)
  - [`validate_cep`](src\smart_core_assistant_painel\app\ui\clientes\models.py#L52) (function)
  - [`Contato`](src\smart_core_assistant_painel\app\ui\clientes\models.py#L65) (class)
  - [`Cliente`](src\smart_core_assistant_painel\app\ui\clientes\models.py#L151) (class)
  - [`ModelsStrTests`](src\smart_core_assistant_painel\app\trello_sync\tests\test_models.py#L6) (class)
  - [`EvolutionMessageData`](src\smart_core_assistant_painel\app\evolution_sync\domain\schemas.py#L6) (class)
  - [`EvolutionContactData`](src\smart_core_assistant_painel\app\evolution_sync\domain\schemas.py#L85) (class)
  - [`EvolutionProfileData`](src\smart_core_assistant_painel\app\evolution_sync\domain\schemas.py#L185) (class)
  - [`EvolutionWebhookEnvelope`](src\smart_core_assistant_painel\app\evolution_sync\domain\schemas.py#L216) (class)
  - [`TestTreinamentoTreinamentos`](src\smart_core_assistant_painel\app\ui\treinamento\tests\test_treinamento_models.py#L20) (class)
  - [`TestTreinamentoValidators`](src\smart_core_assistant_painel\app\ui\treinamento\tests\test_treinamento_models.py#L48) (class)
  - [`TestTreinamentoTreinamentosAdvanced`](src\smart_core_assistant_painel\app\ui\treinamento\tests\test_treinamento_models.py#L70) (class)
  - [`TestQueryCompose`](src\smart_core_assistant_painel\app\ui\treinamento\tests\test_treinamento_models.py#L97) (class)
  - [`mock_departamento`](src\smart_core_assistant_painel\app\ui\atendimentos\tests\test_models.py#L30) (function)
  - [`mock_fluxo`](src\smart_core_assistant_painel\app\ui\atendimentos\tests\test_models.py#L39) (function)
  - [`mock_etapa_fila`](src\smart_core_assistant_painel\app\ui\atendimentos\tests\test_models.py#L50) (function)
  - [`mock_etapa_atendimento`](src\smart_core_assistant_painel\app\ui\atendimentos\tests\test_models.py#L65) (function)
  - [`mock_contato`](src\smart_core_assistant_painel\app\ui\atendimentos\tests\test_models.py#L80) (function)
  - [`mock_atendente`](src\smart_core_assistant_painel\app\ui\atendimentos\tests\test_models.py#L90) (function)
  - [`atendimento_instance`](src\smart_core_assistant_painel\app\ui\atendimentos\tests\test_models.py#L101) (function)
  - [`TestAtendimentoModel`](src\smart_core_assistant_painel\app\ui\atendimentos\tests\test_models.py#L109) (class)
  - [`TestMensagemModel`](src\smart_core_assistant_painel\app\ui\atendimentos\tests\test_models.py#L365) (class)
  - [`TestAtendimentoFunctions`](src\smart_core_assistant_painel\app\ui\atendimentos\tests\test_models.py#L410) (class)
  - [`TestClientesContato`](src\smart_core_assistant_painel\app\ui\clientes\tests\test_clientes_models.py#L8) (class)
  - [`TestClientesCliente`](src\smart_core_assistant_painel\app\ui\clientes\tests\test_clientes_models.py#L34) (class)
  - [`test_evolution_message_data_from_dict_conversation`](src\smart_core_assistant_painel\app\evolution_sync\tests\domain\test_schemas.py#L9) (function)
  - [`test_evolution_message_data_from_dict_extended_text`](src\smart_core_assistant_painel\app\evolution_sync\tests\domain\test_schemas.py#L29) (function)
  - [`test_evolution_message_data_to_dict`](src\smart_core_assistant_painel\app\evolution_sync\tests\domain\test_schemas.py#L43) (function)
  - [`test_evolution_contact_data_from_dict`](src\smart_core_assistant_painel\app\evolution_sync\tests\domain\test_schemas.py#L59) (function)
  - [`test_evolution_contact_data_from_dict_lid`](src\smart_core_assistant_painel\app\evolution_sync\tests\domain\test_schemas.py#L73) (function)
  - [`test_evolution_contact_data_to_dict`](src\smart_core_assistant_painel\app\evolution_sync\tests\domain\test_schemas.py#L86) (function)
  - [`test_evolution_profile_data_from_dict`](src\smart_core_assistant_painel\app\evolution_sync\tests\domain\test_schemas.py#L99) (function)
  - [`test_evolution_profile_data_to_dict`](src\smart_core_assistant_painel\app\evolution_sync\tests\domain\test_schemas.py#L107) (function)
  - [`test_evolution_webhook_envelope_from_dict`](src\smart_core_assistant_painel\app\evolution_sync\tests\domain\test_schemas.py#L115) (function)
  - [`test_evolution_webhook_envelope_from_dict_single`](src\smart_core_assistant_painel\app\evolution_sync\tests\domain\test_schemas.py#L145) (function)
  - [`test_evolution_webhook_envelope_from_dict_single_with_list_data`](src\smart_core_assistant_painel\app\evolution_sync\tests\domain\test_schemas.py#L160) (function)
  - [`test_evolution_webhook_envelope_from_dict_batch`](src\smart_core_assistant_painel\app\evolution_sync\tests\domain\test_schemas.py#L182) (function)
  - [`test_evolution_webhook_envelope_to_dict`](src\smart_core_assistant_painel\app\evolution_sync\tests\domain\test_schemas.py#L204) (function)
  - [`test_evolution_contact_data_is_group`](src\smart_core_assistant_painel\app\evolution_sync\tests\domain\test_schemas.py#L221) (function)
  - [`test_pydantic_model_docstring_generated_from_jsons`](tests\modules\ai_engine\features\analise_previa_mensagem\datasource\langchain_pydantic\test_pydantic_model_factory_docs.py#L9) (function)
  - [`test_pydantic_model_schema_unchanged_no_confidence`](tests\modules\ai_engine\features\analise_previa_mensagem\datasource\langchain_pydantic\test_pydantic_model_factory_docs.py#L77) (function)
  - [`TestPydanticModelFactory`](tests\modules\ai_engine\features\analise_previa_mensagem\datasource\langchain_pydantic\test_pydantic_model_factory.py#L14) (class)
  - [`TestCreateDynamicPydanticModel`](tests\modules\ai_engine\features\analise_previa_mensagem\datasource\langchain_pydantic\test_pydantic_model_factory.py#L208) (class)
  - [`MessageData`](src\smart_core_assistant_painel\modules\ai_engine\features\load_mensage_data\domain\model\message_data.py#L15) (class)
  - [`build_analise_previa_model`](src\smart_core_assistant_painel\modules\ai_engine\features\analise_previa_mensagem\datasource\analise_previa_langchain\pydantic_model_builder.py#L228) (function)
  - [`AnalisePreviaMensagem`](src\smart_core_assistant_painel\modules\ai_engine\features\analise_previa_mensagem\domain\interface\analise_previa_mensagem.py#L16) (class)

### Components
UI components and views
- **Directories**: `src\smart_core_assistant_painel\app\evolution_sync`, `src\smart_core_assistant_painel\app\settings_manager`, `src\smart_core_assistant_painel\app\ui\usuarios`, `src\smart_core_assistant_painel\app\ui\treinamento`, `src\smart_core_assistant_painel\app\ui\operacional`, `src\smart_core_assistant_painel\app\ui\core`, `src\smart_core_assistant_painel\app\ui\clientes`, `src\smart_core_assistant_painel\app\tenants\views`, `src\smart_core_assistant_painel\app\evolution_sync\tests`, `src\smart_core_assistant_painel\app\ui\usuarios\tests`, `src\smart_core_assistant_painel\app\ui\treinamento\tests`, `src\smart_core_assistant_painel\app\ui\operacional\tests`, `src\smart_core_assistant_painel\app\ui\clientes\tests`, `src\smart_core_assistant_painel\app\tenants\views\backoffice`
- **Symbols**: 63 total, 54 exported
- **Key exports**:
  - [`webhook`](src\smart_core_assistant_painel\app\evolution_sync\views.py#L22) (function)
  - [`cadastro`](src\smart_core_assistant_painel\app\ui\usuarios\views.py#L27) (function)
  - [`login`](src\smart_core_assistant_painel\app\ui\usuarios\views.py#L76) (function)
  - [`logout_view`](src\smart_core_assistant_painel\app\ui\usuarios\views.py#L134) (function)
  - [`permissoes`](src\smart_core_assistant_painel\app\ui\usuarios\views.py#L144) (function)
  - [`tornar_gerente`](src\smart_core_assistant_painel\app\ui\usuarios\views.py#L153) (function)
  - [`dashboard_gerente`](src\smart_core_assistant_painel\app\ui\usuarios\views.py#L168) (function)
  - [`treinar_ia`](src\smart_core_assistant_painel\app\ui\treinamento\views.py#L69) (function)
  - [`pre_processamento`](src\smart_core_assistant_painel\app\ui\treinamento\views.py#L197) (function)
  - [`verificar_treinamentos_vetorizados`](src\smart_core_assistant_painel\app\ui\treinamento\views.py#L315) (function)
  - [`verificar_query_compose`](src\smart_core_assistant_painel\app\ui\treinamento\views.py#L385) (function)
  - [`cadastrar_query_compose`](src\smart_core_assistant_painel\app\ui\treinamento\views.py#L452) (function)
  - [`health_check`](src\smart_core_assistant_painel\app\ui\core\views.py#L85) (function)
  - [`LandingPageView`](src\smart_core_assistant_painel\app\ui\core\views.py#L101) (class)
  - [`dashboard`](src\smart_core_assistant_painel\app\ui\core\views.py#L115) (function)
  - [`clickup_callback`](src\smart_core_assistant_painel\app\ui\core\views.py#L129) (function)
  - [`custom_page_not_found`](src\smart_core_assistant_painel\app\ui\core\views.py#L169) (function)
  - [`custom_permission_denied`](src\smart_core_assistant_painel\app\ui\core\views.py#L176) (function)
  - [`custom_server_error`](src\smart_core_assistant_painel\app\ui\core\views.py#L183) (function)
  - [`OnboardingSessionMixin`](src\smart_core_assistant_painel\app\tenants\views\onboarding.py#L13) (class)
  - [`Step1TenantView`](src\smart_core_assistant_painel\app\tenants\views\onboarding.py#L29) (class)
  - [`Step2PaymentView`](src\smart_core_assistant_painel\app\tenants\views\onboarding.py#L46) (class)
  - [`Step3ConfigView`](src\smart_core_assistant_painel\app\tenants\views\onboarding.py#L71) (class)
  - [`Step4ProvisionView`](src\smart_core_assistant_painel\app\tenants\views\onboarding.py#L90) (class)
  - [`CheckSlugView`](src\smart_core_assistant_painel\app\tenants\views\onboarding.py#L118) (class)
  - [`TenantSignupView`](src\smart_core_assistant_painel\app\tenants\views\legacy_views.py#L46) (class)
  - [`DashboardView`](src\smart_core_assistant_painel\app\tenants\views\legacy_views.py#L94) (class)
  - [`BaseTenantConfigView`](src\smart_core_assistant_painel\app\tenants\views\legacy_views.py#L116) (class)
  - [`EvolutionConfigView`](src\smart_core_assistant_painel\app\tenants\views\legacy_views.py#L200) (class)
  - [`TrelloConfigView`](src\smart_core_assistant_painel\app\tenants\views\legacy_views.py#L211) (class)
  - [`AIConfigView`](src\smart_core_assistant_painel\app\tenants\views\legacy_views.py#L240) (class)
  - [`DatabaseConfigView`](src\smart_core_assistant_painel\app\tenants\views\legacy_views.py#L252) (class)
  - [`TestConnectionView`](src\smart_core_assistant_painel\app\tenants\views\legacy_views.py#L274) (class)
  - [`RunMigrationsView`](src\smart_core_assistant_painel\app\tenants\views\legacy_views.py#L324) (class)
  - [`ConfigDebugView`](src\smart_core_assistant_painel\app\tenants\views\legacy_views.py#L354) (class)
  - [`RegisterTrelloWebhookView`](src\smart_core_assistant_painel\app\tenants\views\legacy_views.py#L535) (class)
  - [`DeleteTrelloWebhookView`](src\smart_core_assistant_painel\app\tenants\views\legacy_views.py#L589) (class)
  - [`list_users`](src\smart_core_assistant_painel\app\tenants\views\invites.py#L17) (function)
  - [`invite_user`](src\smart_core_assistant_painel\app\tenants\views\invites.py#L67) (function)
  - [`resend_invite`](src\smart_core_assistant_painel\app\tenants\views\invites.py#L161) (function)
  - [`activate_account`](src\smart_core_assistant_painel\app\tenants\views\invites.py#L272) (function)
  - [`edit_permissions`](src\smart_core_assistant_painel\app\tenants\views\invites.py#L351) (function)
  - [`factory`](src\smart_core_assistant_painel\app\evolution_sync\tests\test_views.py#L11) (function)
  - [`test_webhook_view_success`](src\smart_core_assistant_painel\app\evolution_sync\tests\test_views.py#L19) (function)
  - [`test_webhook_view_invalid_method`](src\smart_core_assistant_painel\app\evolution_sync\tests\test_views.py#L44) (function)
  - [`test_webhook_view_invalid_json`](src\smart_core_assistant_painel\app\evolution_sync\tests\test_views.py#L52) (function)
  - [`TestUsuariosAppViews`](src\smart_core_assistant_painel\app\ui\usuarios\tests\test_usuarios_views.py#L9) (class)
  - [`TestTreinamentoViews`](src\smart_core_assistant_painel\app\ui\treinamento\tests\test_treinamento_views.py#L16) (class)
  - [`TestPreProcessamentoViews`](src\smart_core_assistant_painel\app\ui\treinamento\tests\test_treinamento_views.py#L257) (class)
  - [`TestVerificarTreinamentosViews`](src\smart_core_assistant_painel\app\ui\treinamento\tests\test_treinamento_views.py#L497) (class)
  - [`TestOperacionalAppViews`](src\smart_core_assistant_painel\app\ui\operacional\tests\test_operacional_views.py#L6) (class)
  - [`TestClientesAppViews`](src\smart_core_assistant_painel\app\ui\clientes\tests\test_clientes_views.py#L6) (class)
  - [`RegisterPaymentView`](src\smart_core_assistant_painel\app\tenants\views\backoffice\register_payment.py#L10) (class)
  - [`BackofficeDashboardView`](src\smart_core_assistant_painel\app\tenants\views\backoffice\dashboard.py#L9) (class)

### Utils
Shared utilities and helpers
- **Directories**: `src\smart_core_assistant_painel\modules\initial_loading\utils`, `src\smart_core_assistant_painel\modules\ai_engine\utils`, `src\smart_core_assistant_painel\app\tenants\utils`
- **Symbols**: 27 total, 27 exported
- **Key exports**:
  - [`FirebaseInitParameters`](src\smart_core_assistant_painel\modules\initial_loading\utils\parameters.py#L18) (class)
  - [`FirebaseInitError`](src\smart_core_assistant_painel\modules\initial_loading\utils\erros.py#L13) (class)
  - [`APMTuple`](src\smart_core_assistant_painel\modules\ai_engine\utils\types.py#L46) (class)
  - [`AMTuple`](src\smart_core_assistant_painel\modules\ai_engine\utils\types.py#L107) (class)
  - [`RespostaBot`](src\smart_core_assistant_painel\modules\ai_engine\utils\types.py#L123) (class)
  - [`AnaliseAvaliacao`](src\smart_core_assistant_painel\modules\ai_engine\utils\types.py#L163) (class)
  - [`DataMensageParameters`](src\smart_core_assistant_painel\modules\ai_engine\utils\parameters.py#L25) (class)
  - [`LoadDocumentFileParameters`](src\smart_core_assistant_painel\modules\ai_engine\utils\parameters.py#L42) (class)
  - [`LoadDocumentConteudoParameters`](src\smart_core_assistant_painel\modules\ai_engine\utils\parameters.py#L65) (class)
  - [`LlmParameters`](src\smart_core_assistant_painel\modules\ai_engine\utils\parameters.py#L87) (class)
  - [`AnalisePreviaMensagemParameters`](src\smart_core_assistant_painel\modules\ai_engine\utils\parameters.py#L170) (class)
  - [`GenerateEmbeddingsParameters`](src\smart_core_assistant_painel\modules\ai_engine\utils\parameters.py#L194) (class)
  - [`SearchSimilarEmbeddingsParameters`](src\smart_core_assistant_painel\modules\ai_engine\utils\parameters.py#L211) (class)
  - [`GenerateChunksParameters`](src\smart_core_assistant_painel\modules\ai_engine\utils\parameters.py#L232) (class)
  - [`AnaliseMensageParameters`](src\smart_core_assistant_painel\modules\ai_engine\utils\parameters.py#L251) (class)
  - [`AnaliseAvaliacaoParameters`](src\smart_core_assistant_painel\modules\ai_engine\utils\parameters.py#L280) (class)
  - [`HtmlStrError`](src\smart_core_assistant_painel\modules\ai_engine\utils\erros.py#L14) (class)
  - [`LlmError`](src\smart_core_assistant_painel\modules\ai_engine\utils\erros.py#L25) (class)
  - [`DocumentError`](src\smart_core_assistant_painel\modules\ai_engine\utils\erros.py#L36) (class)
  - [`DataMessageError`](src\smart_core_assistant_painel\modules\ai_engine\utils\erros.py#L47) (class)
  - [`EmbeddingError`](src\smart_core_assistant_painel\modules\ai_engine\utils\erros.py#L58) (class)
  - [`GenerateChunksError`](src\smart_core_assistant_painel\modules\ai_engine\utils\erros.py#L69) (class)
  - [`AnaliseMensageError`](src\smart_core_assistant_painel\modules\ai_engine\utils\erros.py#L80) (class)
  - [`AnaliseAvaliacaoError`](src\smart_core_assistant_painel\modules\ai_engine\utils\erros.py#L88) (class)
  - [`get_fernet`](src\smart_core_assistant_painel\app\tenants\utils\encryption.py#L9) (function)
  - [`encrypt_value`](src\smart_core_assistant_painel\app\tenants\utils\encryption.py#L17) (function)
  - [`decrypt_value`](src\smart_core_assistant_painel\app\tenants\utils\encryption.py#L29) (function)


## Detected Design Patterns
| Pattern | Confidence | Locations | Description |
|---------|------------|-----------|-------------|
| Factory | 90% | `TestPydanticModelFactory` ([test_pydantic_model_factory.py](tests\modules\ai_engine\features\analise_previa_mensagem\datasource\langchain_pydantic\test_pydantic_model_factory.py)) | Creates instances of related objects without specifying concrete classes |
| Singleton | 70% | `TenantEvolutionInstanceAdmin` ([tenant_admin.py](src\smart_core_assistant_painel\app\evolution_sync\tenant_admin.py)), `EvolutionInstance` ([models.py](src\smart_core_assistant_painel\app\evolution_sync\models.py)), `EvolutionInstanceAdmin` ([admin.py](src\smart_core_assistant_painel\app\evolution_sync\admin.py)), `TenantAppInstanceAdmin` ([tenant_admin.py](src\smart_core_assistant_painel\app\ui\operacional\tenant_admin.py)), `AppInstance` ([models.py](src\smart_core_assistant_painel\app\ui\operacional\models.py)), `AppInstanceAdmin` ([admin.py](src\smart_core_assistant_painel\app\ui\operacional\admin.py)) | Ensures a class has only one instance |
| Service Layer | 85% | `TreinamentoService` ([services.py](src\smart_core_assistant_painel\app\ui\treinamento\services.py)), `WebhookProcessingService` ([webhook_processing_service.py](src\smart_core_assistant_painel\app\trello_sync\services\webhook_processing_service.py)), `TicketSyncService` ([ticket_sync_service.py](src\smart_core_assistant_painel\app\trello_sync\services\ticket_sync_service.py)), `MemberSyncService` ([member_sync_service.py](src\smart_core_assistant_painel\app\trello_sync\services\member_sync_service.py)), `FlowSyncService` ([flow_sync_service.py](src\smart_core_assistant_painel\app\trello_sync\services\flow_sync_service.py)), `TenantProvisioningService` ([provisioning.py](src\smart_core_assistant_painel\app\tenants\services\provisioning.py)), `EvolutionWhatsAppService` ([evolution_api.py](src\smart_core_assistant_painel\app\evolution_sync\services\evolution_api.py)), `TestInMemoryUnifiedDataService` ([test_unifield_data_services_datasource.py](tests\modules\services\features\unifield_data_services\datasource\test_unifield_data_services_datasource.py)), `TestTrelloUnifiedDataService` ([test_trello_adapter.py](tests\modules\services\features\unifield_data_services\datasource\test_trello_adapter.py)), `TestClicupUnifiedDataService` ([test_clicup_adapter.py](tests\modules\services\features\unifield_data_services\datasource\test_clicup_adapter.py)), `_InMemoryUnifiedDataService` ([unifield_data_services_datasource.py](src\smart_core_assistant_painel\modules\services\features\unifield_data_services\datasource\unifield_data_services_datasource.py)), `TrelloUnifiedDataService` ([trello_adapter.py](src\smart_core_assistant_painel\modules\services\features\unifield_data_services\datasource\trello_adapter.py)), `NotionUnifiedDataService` ([notion_adapter.py](src\smart_core_assistant_painel\modules\services\features\unifield_data_services\datasource\notion_adapter.py)), `ClicupUnifiedDataService` ([clicup_adapter.py](src\smart_core_assistant_painel\modules\services\features\unifield_data_services\datasource\clicup_adapter.py)), `UnifiedDataService` ([unified_data_service.py](src\smart_core_assistant_painel\modules\services\features\unifield_data_services\domain\interface\unified_data_service.py)) | Encapsulates business logic in service classes |

## Entry Points
- *No entry points detected.*

## Public API
| Symbol | Type | Location |
| --- | --- | --- |
| [`activate_account`](src\smart_core_assistant_painel\app\tenants\views\invites.py#L272) | function | src\smart_core_assistant_painel\app\tenants\views\invites.py:272 |
| [`AdminStaffRequiredMiddleware`](src\smart_core_assistant_painel\app\ui\core\middleware.py#L8) | class | src\smart_core_assistant_painel\app\ui\core\middleware.py:8 |
| [`AIConfigView`](src\smart_core_assistant_painel\app\tenants\views\legacy_views.py#L240) | class | src\smart_core_assistant_painel\app\tenants\views\legacy_views.py:240 |
| [`AMTuple`](src\smart_core_assistant_painel\modules\ai_engine\utils\types.py#L107) | class | src\smart_core_assistant_painel\modules\ai_engine\utils\types.py:107 |
| [`AnaliseAvaliacao`](src\smart_core_assistant_painel\modules\ai_engine\utils\types.py#L163) | class | src\smart_core_assistant_painel\modules\ai_engine\utils\types.py:163 |
| [`AnaliseAvaliacaoDatasource`](src\smart_core_assistant_painel\modules\ai_engine\features\analise_avaliacao\datasource\analise_avaliacao_datasource.py#L30) | class | src\smart_core_assistant_painel\modules\ai_engine\features\analise_avaliacao\datasource\analise_avaliacao_datasource.py:30 |
| [`AnaliseAvaliacaoError`](src\smart_core_assistant_painel\modules\ai_engine\utils\erros.py#L88) | class | src\smart_core_assistant_painel\modules\ai_engine\utils\erros.py:88 |
| [`AnaliseAvaliacaoParameters`](src\smart_core_assistant_painel\modules\ai_engine\utils\parameters.py#L280) | class | src\smart_core_assistant_painel\modules\ai_engine\utils\parameters.py:280 |
| [`AnaliseAvaliacaoUsecase`](src\smart_core_assistant_painel\modules\ai_engine\features\analise_avaliacao\domain\usecase\analise_avaliacao_usecase.py#L18) | class | src\smart_core_assistant_painel\modules\ai_engine\features\analise_avaliacao\domain\usecase\analise_avaliacao_usecase.py:18 |
| [`AnaliseConteudoLangchainDatasource`](src\smart_core_assistant_painel\modules\ai_engine\features\analise_conteudo\datasource\analise_conteudo_langchain_datasource.py#L13) | class | src\smart_core_assistant_painel\modules\ai_engine\features\analise_conteudo\datasource\analise_conteudo_langchain_datasource.py:13 |
| [`AnaliseConteudoUseCase`](src\smart_core_assistant_painel\modules\ai_engine\features\analise_conteudo\domain\usecase\analise_conteudo_usecase.py#L11) | class | src\smart_core_assistant_painel\modules\ai_engine\features\analise_conteudo\domain\usecase\analise_conteudo_usecase.py:11 |
| [`AnaliseMensageDatasource`](src\smart_core_assistant_painel\modules\ai_engine\features\analise_mensage\datasource\analise_mensage_datasource.py#L19) | class | src\smart_core_assistant_painel\modules\ai_engine\features\analise_mensage\datasource\analise_mensage_datasource.py:19 |
| [`AnaliseMensageError`](src\smart_core_assistant_painel\modules\ai_engine\utils\erros.py#L80) | class | src\smart_core_assistant_painel\modules\ai_engine\utils\erros.py:80 |
| [`AnaliseMensageParameters`](src\smart_core_assistant_painel\modules\ai_engine\utils\parameters.py#L251) | class | src\smart_core_assistant_painel\modules\ai_engine\utils\parameters.py:251 |
| [`AnaliseMensageUseCase`](src\smart_core_assistant_painel\modules\ai_engine\features\analise_mensage\domain\usecase\analise_mensage_usecase.py#L13) | class | src\smart_core_assistant_painel\modules\ai_engine\features\analise_mensage\domain\usecase\analise_mensage_usecase.py:13 |
| [`AnalisePreviaLangchainDatasource`](src\smart_core_assistant_painel\modules\ai_engine\features\analise_previa_mensagem\datasource\analise_previa_langchain\analise_previa_langchain_datasource.py#L27) | class | src\smart_core_assistant_painel\modules\ai_engine\features\analise_previa_mensagem\datasource\analise_previa_langchain\analise_previa_langchain_datasource.py:27 |
| [`AnalisePreviaMensagem`](src\smart_core_assistant_painel\modules\ai_engine\features\analise_previa_mensagem\domain\interface\analise_previa_mensagem.py#L16) | class | src\smart_core_assistant_painel\modules\ai_engine\features\analise_previa_mensagem\domain\interface\analise_previa_mensagem.py:16 |
| [`AnalisePreviaMensagemLangchain`](src\smart_core_assistant_painel\modules\ai_engine\features\analise_previa_mensagem\datasource\analise_previa_langchain\analise_previa_mensagem_langchain.py#L17) | class | src\smart_core_assistant_painel\modules\ai_engine\features\analise_previa_mensagem\datasource\analise_previa_langchain\analise_previa_mensagem_langchain.py:17 |
| [`AnalisePreviaMensagemParameters`](src\smart_core_assistant_painel\modules\ai_engine\utils\parameters.py#L170) | class | src\smart_core_assistant_painel\modules\ai_engine\utils\parameters.py:170 |
| [`AnalisePreviaMensagemUsecase`](src\smart_core_assistant_painel\modules\ai_engine\features\analise_previa_mensagem\domain\usecase\analise_previa_mensagem_usecase.py#L16) | class | src\smart_core_assistant_painel\modules\ai_engine\features\analise_previa_mensagem\domain\usecase\analise_previa_mensagem_usecase.py:16 |
| [`APMTuple`](src\smart_core_assistant_painel\modules\ai_engine\utils\types.py#L46) | class | src\smart_core_assistant_painel\modules\ai_engine\utils\types.py:46 |
| [`append_text`](scripts\automacao\new_feature_script.py#L61) | function | scripts\automacao\new_feature_script.py:61 |
| [`AppInstance`](src\smart_core_assistant_painel\app\ui\operacional\models.py#L432) | class | src\smart_core_assistant_painel\app\ui\operacional\models.py:432 |
| [`AppInstanceAdmin`](src\smart_core_assistant_painel\app\ui\operacional\admin.py#L186) | class | src\smart_core_assistant_painel\app\ui\operacional\admin.py:186 |
| [`Atendente`](src\smart_core_assistant_painel\app\ui\operacional\models.py#L210) | class | src\smart_core_assistant_painel\app\ui\operacional\models.py:210 |
| [`atendente_created_invite_trello`](src\smart_core_assistant_painel\app\trello_sync\signals.py#L124) | function | src\smart_core_assistant_painel\app\trello_sync\signals.py:124 |
| [`atendente_deleted_remove_member_trello`](src\smart_core_assistant_painel\app\trello_sync\signals.py#L137) | function | src\smart_core_assistant_painel\app\trello_sync\signals.py:137 |
| [`AtendenteAdmin`](src\smart_core_assistant_painel\app\ui\operacional\admin.py#L25) | class | src\smart_core_assistant_painel\app\ui\operacional\admin.py:25 |
| [`Atendimento`](src\smart_core_assistant_painel\app\ui\atendimentos\models.py#L88) | class | src\smart_core_assistant_painel\app\ui\atendimentos\models.py:88 |
| [`atendimento_cancelado_move_to_cancelado`](src\smart_core_assistant_painel\app\trello_sync\signals.py#L419) | function | src\smart_core_assistant_painel\app\trello_sync\signals.py:419 |
| [`atendimento_capture_old_atendente`](src\smart_core_assistant_painel\app\trello_sync\signals.py#L171) | function | src\smart_core_assistant_painel\app\trello_sync\signals.py:171 |
| [`atendimento_capture_old_etapa`](src\smart_core_assistant_painel\app\trello_sync\signals.py#L194) | function | src\smart_core_assistant_painel\app\trello_sync\signals.py:194 |
| [`atendimento_created_sync_trello`](src\smart_core_assistant_painel\app\trello_sync\signals.py#L109) | function | src\smart_core_assistant_painel\app\trello_sync\signals.py:109 |
| [`atendimento_deleted_archive_card`](src\smart_core_assistant_painel\app\trello_sync\signals.py#L504) | function | src\smart_core_assistant_painel\app\trello_sync\signals.py:504 |
| [`atendimento_etapa_updated_move_card`](src\smart_core_assistant_painel\app\trello_sync\signals.py#L217) | function | src\smart_core_assistant_painel\app\trello_sync\signals.py:217 |
| [`atendimento_instance`](src\smart_core_assistant_painel\app\ui\atendimentos\tests\test_models.py#L101) | function | src\smart_core_assistant_painel\app\ui\atendimentos\tests\test_models.py:101 |
| [`atendimento_pendencia_move_to_pendencia`](src\smart_core_assistant_painel\app\trello_sync\signals.py#L335) | function | src\smart_core_assistant_painel\app\trello_sync\signals.py:335 |
| [`atendimento_resolvido_move_to_resolvido`](src\smart_core_assistant_painel\app\trello_sync\signals.py#L245) | function | src\smart_core_assistant_painel\app\trello_sync\signals.py:245 |
| [`atendimento_updated_assign_member_trello`](src\smart_core_assistant_painel\app\trello_sync\signals.py#L150) | function | src\smart_core_assistant_painel\app\trello_sync\signals.py:150 |
| [`AtendimentoAdmin`](src\smart_core_assistant_painel\app\ui\atendimentos\admin.py#L60) | class | src\smart_core_assistant_painel\app\ui\atendimentos\admin.py:60 |
| [`AtendimentosConfig`](src\smart_core_assistant_painel\app\ui\atendimentos\apps.py#L5) | class | src\smart_core_assistant_painel\app\ui\atendimentos\apps.py:5 |
| [`AttendanceOrchestrator`](src\smart_core_assistant_painel\app\ui\atendimentos\services\attendance_orchestrator.py#L34) | class | src\smart_core_assistant_painel\app\ui\atendimentos\services\attendance_orchestrator.py:34 |
| [`AttendanceOrchestratorInterface`](src\smart_core_assistant_painel\app\ui\atendimentos\services\interfaces.py#L126) | class | src\smart_core_assistant_painel\app\ui\atendimentos\services\interfaces.py:126 |
| [`AttendanceStructureManager`](src\smart_core_assistant_painel\app\ui\atendimentos\services\attendance_structure_manager.py#L23) | class | src\smart_core_assistant_painel\app\ui\atendimentos\services\attendance_structure_manager.py:23 |
| [`AttendanceStructureManagerInterface`](src\smart_core_assistant_painel\app\ui\atendimentos\services\interfaces.py#L56) | class | src\smart_core_assistant_painel\app\ui\atendimentos\services\interfaces.py:56 |
| [`BackofficeDashboardView`](src\smart_core_assistant_painel\app\tenants\views\backoffice\dashboard.py#L9) | class | src\smart_core_assistant_painel\app\tenants\views\backoffice\dashboard.py:9 |
| [`BaseTenantConfigView`](src\smart_core_assistant_painel\app\tenants\views\legacy_views.py#L116) | class | src\smart_core_assistant_painel\app\tenants\views\legacy_views.py:116 |
| [`BaseTenantModelAdmin`](src\smart_core_assistant_painel\app\tenants\admin_mixins.py#L107) | class | src\smart_core_assistant_painel\app\tenants\admin_mixins.py:107 |
| [`BotRulesEngine`](src\smart_core_assistant_painel\app\ui\atendimentos\services\bot_rules_engine.py#L19) | class | src\smart_core_assistant_painel\app\ui\atendimentos\services\bot_rules_engine.py:19 |
| [`BotRulesEngineInterface`](src\smart_core_assistant_painel\app\ui\atendimentos\services\interfaces.py#L96) | class | src\smart_core_assistant_painel\app\ui\atendimentos\services\interfaces.py:96 |
| [`build_analise_previa_model`](src\smart_core_assistant_painel\modules\ai_engine\features\analise_previa_mensagem\datasource\analise_previa_langchain\pydantic_model_builder.py#L228) | function | src\smart_core_assistant_painel\modules\ai_engine\features\analise_previa_mensagem\datasource\analise_previa_langchain\pydantic_model_builder.py:228 |
| [`build_facade_imports`](scripts\automacao\new_feature_script.py#L172) | function | scripts\automacao\new_feature_script.py:172 |
| [`build_facade_method`](scripts\automacao\new_feature_script.py#L202) | function | scripts\automacao\new_feature_script.py:202 |
| [`build_fixture_paths`](scripts\temp\loaddata_remoto.py#L113) | function | scripts\temp\loaddata_remoto.py:113 |
| [`buscar_atendimento_ativo`](src\smart_core_assistant_painel\app\ui\atendimentos\models.py#L1333) | function | src\smart_core_assistant_painel\app\ui\atendimentos\models.py:1333 |
| [`buscar_atendimento_ativo_por_contato`](src\smart_core_assistant_painel\app\ui\atendimentos\models.py#L1419) | function | src\smart_core_assistant_painel\app\ui\atendimentos\models.py:1419 |
| [`buscar_e_preencher_endereco`](src\smart_core_assistant_painel\app\ui\clientes\signals.py#L34) | function | src\smart_core_assistant_painel\app\ui\clientes\signals.py:34 |
| [`cadastrar_query_compose`](src\smart_core_assistant_painel\app\ui\treinamento\views.py#L452) | function | src\smart_core_assistant_painel\app\ui\treinamento\views.py:452 |
| [`cadastro`](src\smart_core_assistant_painel\app\ui\usuarios\views.py#L27) | function | src\smart_core_assistant_painel\app\ui\usuarios\views.py:27 |
| [`camel_case`](scripts\automacao\new_feature_script.py#L27) | function | scripts\automacao\new_feature_script.py:27 |
| [`can_view_module`](src\smart_core_assistant_painel\app\tenants\templatetags\permission_tags.py#L8) | function | src\smart_core_assistant_painel\app\tenants\templatetags\permission_tags.py:8 |
| [`categorize_prompts`](scripts\temp\extrair_prompts_remote_config.py#L91) | function | scripts\temp\extrair_prompts_remote_config.py:91 |
| [`check_celery_inspect`](teste_debug\check_treinamento_celery.py#L158) | function | teste_debug\check_treinamento_celery.py:158 |
| [`check_celery_results`](teste_debug\check_treinamento_celery.py#L82) | function | teste_debug\check_treinamento_celery.py:82 |
| [`check_redis_connection`](teste_debug\check_treinamento_celery.py#L139) | function | teste_debug\check_treinamento_celery.py:139 |
| [`check_subscription_expirations`](src\smart_core_assistant_painel\app\tenants\tasks.py#L13) | function | src\smart_core_assistant_painel\app\tenants\tasks.py:13 |
| [`check_treinamentos`](teste_debug\check_treinamento_celery.py#L28) | function | teste_debug\check_treinamento_celery.py:28 |
| [`CheckSlugView`](src\smart_core_assistant_painel\app\tenants\views\onboarding.py#L118) | class | src\smart_core_assistant_painel\app\tenants\views\onboarding.py:118 |
| [`clear_buffer_contact`](src\smart_core_assistant_painel\app\evolution_sync\services\message_buffer.py#L57) | function | src\smart_core_assistant_painel\app\evolution_sync\services\message_buffer.py:57 |
| [`clear_current_tenant`](src\smart_core_assistant_painel\app\tenants\middleware.py#L25) | function | src\smart_core_assistant_painel\app\tenants\middleware.py:25 |
| [`clear_scheduling_lock`](src\smart_core_assistant_painel\app\evolution_sync\services\message_buffer.py#L49) | function | src\smart_core_assistant_painel\app\evolution_sync\services\message_buffer.py:49 |
| [`clickup_callback`](src\smart_core_assistant_painel\app\ui\core\views.py#L129) | function | src\smart_core_assistant_painel\app\ui\core\views.py:129 |
| [`ClicupUnifiedDataService`](src\smart_core_assistant_painel\modules\services\features\unifield_data_services\datasource\clicup_adapter.py#L25) | class | src\smart_core_assistant_painel\modules\services\features\unifield_data_services\datasource\clicup_adapter.py:25 |
| [`Cliente`](src\smart_core_assistant_painel\app\ui\clientes\models.py#L151) | class | src\smart_core_assistant_painel\app\ui\clientes\models.py:151 |
| [`ClienteAdmin`](src\smart_core_assistant_painel\app\ui\clientes\admin.py#L81) | class | src\smart_core_assistant_painel\app\ui\clientes\admin.py:81 |
| [`ClientesConfig`](src\smart_core_assistant_painel\app\ui\clientes\apps.py#L5) | class | src\smart_core_assistant_painel\app\ui\clientes\apps.py:5 |
| [`ClientesContatoForm`](src\smart_core_assistant_painel\app\ui\clientes\tests\test_clientes_forms.py#L10) | class | src\smart_core_assistant_painel\app\ui\clientes\tests\test_clientes_forms.py:10 |
| [`Command`](src\smart_core_assistant_painel\app\tenants\management\commands\migrate_tenant.py#L17) | class | src\smart_core_assistant_painel\app\tenants\management\commands\migrate_tenant.py:17 |
| [`Command`](src\smart_core_assistant_painel\app\tenants\management\commands\migrate_all_tenants.py#L21) | class | src\smart_core_assistant_painel\app\tenants\management\commands\migrate_all_tenants.py:21 |
| [`Command`](src\smart_core_assistant_painel\app\settings_manager\management\commands\load_core_settings.py#L17) | class | src\smart_core_assistant_painel\app\settings_manager\management\commands\load_core_settings.py:17 |
| [`Command`](src\smart_core_assistant_painel\app\settings_manager\management\commands\import_core_settings.py#L15) | class | src\smart_core_assistant_painel\app\settings_manager\management\commands\import_core_settings.py:15 |
| [`Command`](src\smart_core_assistant_painel\app\settings_manager\management\commands\export_core_settings.py#L13) | class | src\smart_core_assistant_painel\app\settings_manager\management\commands\export_core_settings.py:13 |
| [`Command`](src\smart_core_assistant_painel\app\ui\usuarios\management\commands\seed_dev_data.py#L24) | class | src\smart_core_assistant_painel\app\ui\usuarios\management\commands\seed_dev_data.py:24 |
| [`Command`](src\smart_core_assistant_painel\app\ui\usuarios\management\commands\seed_atendentes_users.py#L27) | class | src\smart_core_assistant_painel\app\ui\usuarios\management\commands\seed_atendentes_users.py:27 |
| [`Command`](src\smart_core_assistant_painel\app\ui\operacional\management\commands\seed_demo_flow.py#L23) | class | src\smart_core_assistant_painel\app\ui\operacional\management\commands\seed_demo_flow.py:23 |
| [`Command`](src\smart_core_assistant_painel\app\ui\operacional\management\commands\seed_comercial_min.py#L39) | class | src\smart_core_assistant_painel\app\ui\operacional\management\commands\seed_comercial_min.py:39 |
| [`ConfigDebugView`](src\smart_core_assistant_painel\app\tenants\views\legacy_views.py#L354) | class | src\smart_core_assistant_painel\app\tenants\views\legacy_views.py:354 |
| [`ConfigLoader`](src\smart_core_assistant_painel\app\tenants\services\config_loader.py#L15) | class | src\smart_core_assistant_painel\app\tenants\services\config_loader.py:15 |
| [`ConfigProvider`](src\smart_core_assistant_painel\modules\services\config\provider.py#L4) | class | src\smart_core_assistant_painel\modules\services\config\provider.py:4 |
| [`ConnectionTester`](src\smart_core_assistant_painel\app\tenants\services\connection_tester.py#L16) | class | src\smart_core_assistant_painel\app\tenants\services\connection_tester.py:16 |
| [`Contato`](src\smart_core_assistant_painel\app\ui\clientes\models.py#L65) | class | src\smart_core_assistant_painel\app\ui\clientes\models.py:65 |
| [`ContatoAdmin`](src\smart_core_assistant_painel\app\ui\clientes\admin.py#L19) | class | src\smart_core_assistant_painel\app\ui\clientes\admin.py:19 |
| [`CoreSettings`](src\smart_core_assistant_painel\app\settings_manager\models.py#L8) | class | src\smart_core_assistant_painel\app\settings_manager\models.py:8 |
| [`CoreSettingsAdmin`](src\smart_core_assistant_painel\app\settings_manager\admin.py#L6) | class | src\smart_core_assistant_painel\app\settings_manager\admin.py:6 |
| [`CoreViewsTestCase`](src\smart_core_assistant_painel\app\ui\core\tests.py#L11) | class | src\smart_core_assistant_painel\app\ui\core\tests.py:11 |
| [`create_default_etapas_fluxo`](src\smart_core_assistant_painel\app\ui\operacional\signals.py#L25) | function | src\smart_core_assistant_painel\app\ui\operacional\signals.py:25 |
| [`create_feature_files`](scripts\automacao\new_feature_script.py#L297) | function | scripts\automacao\new_feature_script.py:297 |
| [`create_orchestrator`](src\smart_core_assistant_painel\app\ui\atendimentos\services\__init__.py#L38) | function | src\smart_core_assistant_painel\app\ui\atendimentos\services\__init__.py:38 |
| [`create_plans`](scripts\temp\populate_plans.py#L17) | function | scripts\temp\populate_plans.py:17 |
| [`create_tenant_subscription`](src\smart_core_assistant_painel\app\tenants\signals.py#L8) | function | src\smart_core_assistant_painel\app\tenants\signals.py:8 |
| [`custom_page_not_found`](src\smart_core_assistant_painel\app\ui\core\views.py#L169) | function | src\smart_core_assistant_painel\app\ui\core\views.py:169 |
| [`custom_permission_denied`](src\smart_core_assistant_painel\app\ui\core\views.py#L176) | function | src\smart_core_assistant_painel\app\ui\core\views.py:176 |
| [`custom_server_error`](src\smart_core_assistant_painel\app\ui\core\views.py#L183) | function | src\smart_core_assistant_painel\app\ui\core\views.py:183 |
| [`dashboard`](src\smart_core_assistant_painel\app\ui\core\views.py#L115) | function | src\smart_core_assistant_painel\app\ui\core\views.py:115 |
| [`dashboard_gerente`](src\smart_core_assistant_painel\app\ui\usuarios\views.py#L168) | function | src\smart_core_assistant_painel\app\ui\usuarios\views.py:168 |
| [`DashboardView`](src\smart_core_assistant_painel\app\tenants\views\legacy_views.py#L94) | class | src\smart_core_assistant_painel\app\tenants\views\legacy_views.py:94 |
| [`DatabaseConfigView`](src\smart_core_assistant_painel\app\tenants\views\legacy_views.py#L252) | class | src\smart_core_assistant_painel\app\tenants\views\legacy_views.py:252 |
| [`DataMensageParameters`](src\smart_core_assistant_painel\modules\ai_engine\utils\parameters.py#L25) | class | src\smart_core_assistant_painel\modules\ai_engine\utils\parameters.py:25 |
| [`DataMessageError`](src\smart_core_assistant_painel\modules\ai_engine\utils\erros.py#L47) | class | src\smart_core_assistant_painel\modules\ai_engine\utils\erros.py:47 |
| [`decrypt_value`](src\smart_core_assistant_painel\app\tenants\utils\encryption.py#L29) | function | src\smart_core_assistant_painel\app\tenants\utils\encryption.py:29 |
| [`delete_webhook`](teste_debug\list_webhooks.py#L42) | function | teste_debug\list_webhooks.py:42 |
| [`DeleteTrelloWebhookView`](src\smart_core_assistant_painel\app\tenants\views\legacy_views.py#L589) | class | src\smart_core_assistant_painel\app\tenants\views\legacy_views.py:589 |
| [`Departamento`](src\smart_core_assistant_painel\app\ui\operacional\models.py#L54) | class | src\smart_core_assistant_painel\app\ui\operacional\models.py:54 |
| [`DepartamentoAdmin`](src\smart_core_assistant_painel\app\ui\operacional\admin.py#L141) | class | src\smart_core_assistant_painel\app\ui\operacional\admin.py:141 |
| [`departamentos_public`](src\smart_core_assistant_painel\app\ui\operacional\views_api.py#L25) | function | src\smart_core_assistant_painel\app\ui\operacional\views_api.py:25 |
| [`DepartamentoSerializer`](src\smart_core_assistant_painel\app\ui\operacional\serializers.py#L14) | class | src\smart_core_assistant_painel\app\ui\operacional\serializers.py:14 |
| [`diagnose`](scripts\temp\diagnostico_config.py#L226) | function | scripts\temp\diagnostico_config.py:226 |
| [`DocumentError`](src\smart_core_assistant_painel\modules\ai_engine\utils\erros.py#L36) | class | src\smart_core_assistant_painel\modules\ai_engine\utils\erros.py:36 |
| [`Documento`](src\smart_core_assistant_painel\app\ui\treinamento\models.py#L106) | class | src\smart_core_assistant_painel\app\ui\treinamento\models.py:106 |
| [`DocumentoAdmin`](src\smart_core_assistant_painel\app\ui\treinamento\admin.py#L187) | class | src\smart_core_assistant_painel\app\ui\treinamento\admin.py:187 |
| [`dump_action`](scripts\config_global\sync_coresettings.py#L71) | function | scripts\config_global\sync_coresettings.py:71 |
| [`edit_permissions`](src\smart_core_assistant_painel\app\tenants\views\invites.py#L351) | function | src\smart_core_assistant_painel\app\tenants\views\invites.py:351 |
| [`EmbeddingError`](src\smart_core_assistant_painel\modules\ai_engine\utils\erros.py#L58) | class | src\smart_core_assistant_painel\modules\ai_engine\utils\erros.py:58 |
| [`encrypt_value`](src\smart_core_assistant_painel\app\tenants\utils\encryption.py#L17) | function | src\smart_core_assistant_painel\app\tenants\utils\encryption.py:17 |
| [`ensure_dir`](scripts\automacao\new_feature_script.py#L46) | function | scripts\automacao\new_feature_script.py:46 |
| [`escape_sql`](scripts\config_global\sync_coresettings.py#L43) | function | scripts\config_global\sync_coresettings.py:43 |
| [`etapa_created_sync_trello`](src\smart_core_assistant_painel\app\trello_sync\signals.py#L52) | function | src\smart_core_assistant_painel\app\trello_sync\signals.py:52 |
| [`etapa_deleted_archive_trello`](src\smart_core_assistant_painel\app\trello_sync\signals.py#L73) | function | src\smart_core_assistant_painel\app\trello_sync\signals.py:73 |
| [`EtapaFluxo`](src\smart_core_assistant_painel\app\ui\operacional\models.py#L559) | class | src\smart_core_assistant_painel\app\ui\operacional\models.py:559 |
| [`EtapaFluxoAdmin`](src\smart_core_assistant_painel\app\ui\operacional\admin.py#L297) | class | src\smart_core_assistant_painel\app\ui\operacional\admin.py:297 |
| [`EtapaFluxoSerializer`](src\smart_core_assistant_painel\app\ui\operacional\serializers.py#L22) | class | src\smart_core_assistant_painel\app\ui\operacional\serializers.py:22 |
| [`EvolutionConfigView`](src\smart_core_assistant_painel\app\tenants\views\legacy_views.py#L200) | class | src\smart_core_assistant_painel\app\tenants\views\legacy_views.py:200 |
| [`EvolutionContact`](src\smart_core_assistant_painel\app\evolution_sync\models.py#L57) | class | src\smart_core_assistant_painel\app\evolution_sync\models.py:57 |
| [`EvolutionContactAdmin`](src\smart_core_assistant_painel\app\evolution_sync\admin.py#L38) | class | src\smart_core_assistant_painel\app\evolution_sync\admin.py:38 |
| [`EvolutionContactData`](src\smart_core_assistant_painel\app\evolution_sync\domain\schemas.py#L85) | class | src\smart_core_assistant_painel\app\evolution_sync\domain\schemas.py:85 |
| [`EvolutionInstance`](src\smart_core_assistant_painel\app\evolution_sync\models.py#L7) | class | src\smart_core_assistant_painel\app\evolution_sync\models.py:7 |
| [`EvolutionInstanceAdmin`](src\smart_core_assistant_painel\app\evolution_sync\admin.py#L21) | class | src\smart_core_assistant_painel\app\evolution_sync\admin.py:21 |
| [`EvolutionMessageData`](src\smart_core_assistant_painel\app\evolution_sync\domain\schemas.py#L6) | class | src\smart_core_assistant_painel\app\evolution_sync\domain\schemas.py:6 |
| [`EvolutionProfileData`](src\smart_core_assistant_painel\app\evolution_sync\domain\schemas.py#L185) | class | src\smart_core_assistant_painel\app\evolution_sync\domain\schemas.py:185 |
| [`EvolutionSyncConfig`](src\smart_core_assistant_painel\app\evolution_sync\apps.py#L4) | class | src\smart_core_assistant_painel\app\evolution_sync\apps.py:4 |
| [`EvolutionWebhookEnvelope`](src\smart_core_assistant_painel\app\evolution_sync\domain\schemas.py#L216) | class | src\smart_core_assistant_painel\app\evolution_sync\domain\schemas.py:216 |
| [`EvolutionWhatsAppService`](src\smart_core_assistant_painel\app\evolution_sync\services\evolution_api.py#L7) | class | src\smart_core_assistant_painel\app\evolution_sync\services\evolution_api.py:7 |
| [`extract_prompts`](scripts\temp\extrair_prompts_remote_config.py#L79) | function | scripts\temp\extrair_prompts_remote_config.py:79 |
| [`factory`](src\smart_core_assistant_painel\app\evolution_sync\tests\test_views.py#L11) | function | src\smart_core_assistant_painel\app\evolution_sync\tests\test_views.py:11 |
| [`FeaturesCompose`](src\smart_core_assistant_painel\modules\initial_loading\features\features_compose.py#L13) | class | src\smart_core_assistant_painel\modules\initial_loading\features\features_compose.py:13 |
| [`FeaturesCompose`](src\smart_core_assistant_painel\modules\ai_engine\features\features_compose.py#L123) | class | src\smart_core_assistant_painel\modules\ai_engine\features\features_compose.py:123 |
| [`FeaturesCompose`](src\smart_core_assistant_painel\modules\services\features\features_compose.py#L27) | class | src\smart_core_assistant_painel\modules\services\features\features_compose.py:27 |
| [`FirebaseInitError`](src\smart_core_assistant_painel\modules\initial_loading\utils\erros.py#L13) | class | src\smart_core_assistant_painel\modules\initial_loading\utils\erros.py:13 |
| [`FirebaseInitParameters`](src\smart_core_assistant_painel\modules\initial_loading\utils\parameters.py#L18) | class | src\smart_core_assistant_painel\modules\initial_loading\utils\parameters.py:18 |
| [`FirebaseInitUseCase`](src\smart_core_assistant_painel\modules\initial_loading\features\firebase_init\domain\usecase\firebase_init_usecase.py#L19) | class | src\smart_core_assistant_painel\modules\initial_loading\features\firebase_init\domain\usecase\firebase_init_usecase.py:19 |
| [`fix_missing_core_settings`](scripts\temp\diagnostico_config.py#L353) | function | scripts\temp\diagnostico_config.py:353 |
| [`fix_permissions`](teste_debug\fix_permissions.py#L15) | function | teste_debug\fix_permissions.py:15 |
| [`FlowSyncService`](src\smart_core_assistant_painel\app\trello_sync\services\flow_sync_service.py#L24) | class | src\smart_core_assistant_painel\app\trello_sync\services\flow_sync_service.py:24 |
| [`fluxo_created_sync_trello`](src\smart_core_assistant_painel\app\trello_sync\signals.py#L39) | function | src\smart_core_assistant_painel\app\trello_sync\signals.py:39 |
| [`fluxo_deleted_archive_trello`](src\smart_core_assistant_painel\app\trello_sync\signals.py#L88) | function | src\smart_core_assistant_painel\app\trello_sync\signals.py:88 |
| [`fluxo_departamento_public`](src\smart_core_assistant_painel\app\ui\operacional\views_api.py#L34) | function | src\smart_core_assistant_painel\app\ui\operacional\views_api.py:34 |
| [`FluxoAtendimento`](src\smart_core_assistant_painel\app\ui\operacional\models.py#L495) | class | src\smart_core_assistant_painel\app\ui\operacional\models.py:495 |
| [`FluxoAtendimentoAdmin`](src\smart_core_assistant_painel\app\ui\operacional\admin.py#L211) | class | src\smart_core_assistant_painel\app\ui\operacional\admin.py:211 |
| [`FluxoAtendimentoSerializer`](src\smart_core_assistant_painel\app\ui\operacional\serializers.py#L40) | class | src\smart_core_assistant_painel\app\ui\operacional\serializers.py:40 |
| [`format_dependencies`](scripts\temp\visualize_tasks.py#L88) | function | scripts\temp\visualize_tasks.py:88 |
| [`gen_datasource_content`](scripts\automacao\new_feature_script.py#L155) | function | scripts\automacao\new_feature_script.py:155 |
| [`gen_error_block`](scripts\automacao\new_feature_script.py#L68) | function | scripts\automacao\new_feature_script.py:68 |
| [`gen_parameters_block`](scripts\automacao\new_feature_script.py#L79) | function | scripts\automacao\new_feature_script.py:79 |
| [`gen_types_block`](scripts\automacao\new_feature_script.py#L94) | function | scripts\automacao\new_feature_script.py:94 |
| [`gen_usecase_content`](scripts\automacao\new_feature_script.py#L114) | function | scripts\automacao\new_feature_script.py:114 |
| [`generate_html`](scripts\temp\generate_proposal_html.py#L23) | function | scripts\temp\generate_proposal_html.py:23 |
| [`GenerateChunksError`](src\smart_core_assistant_painel\modules\ai_engine\utils\erros.py#L69) | class | src\smart_core_assistant_painel\modules\ai_engine\utils\erros.py:69 |
| [`GenerateChunksParameters`](src\smart_core_assistant_painel\modules\ai_engine\utils\parameters.py#L232) | class | src\smart_core_assistant_painel\modules\ai_engine\utils\parameters.py:232 |
| [`GenerateChunksUseCase`](src\smart_core_assistant_painel\modules\ai_engine\features\generate_chunks\domain\usecase\generate_chunks_usecase.py#L22) | class | src\smart_core_assistant_painel\modules\ai_engine\features\generate_chunks\domain\usecase\generate_chunks_usecase.py:22 |
| [`GenerateEmbeddingsLangchainDatasource`](src\smart_core_assistant_painel\modules\ai_engine\features\generate_embeddings\datasource\generate_embeddings_langchain_datasource.py#L18) | class | src\smart_core_assistant_painel\modules\ai_engine\features\generate_embeddings\datasource\generate_embeddings_langchain_datasource.py:18 |
| [`GenerateEmbeddingsParameters`](src\smart_core_assistant_painel\modules\ai_engine\utils\parameters.py#L194) | class | src\smart_core_assistant_painel\modules\ai_engine\utils\parameters.py:194 |
| [`GenerateEmbeddingsUseCase`](src\smart_core_assistant_painel\modules\ai_engine\features\generate_embeddings\domain\usecase\generate_embeddings_usecase.py#L11) | class | src\smart_core_assistant_painel\modules\ai_engine\features\generate_embeddings\domain\usecase\generate_embeddings_usecase.py:11 |
| [`Gerente`](src\smart_core_assistant_painel\app\ui\core\roles.py#L13) | class | src\smart_core_assistant_painel\app\ui\core\roles.py:13 |
| [`get_and_clear_buffer_contact`](src\smart_core_assistant_painel\app\evolution_sync\services\message_buffer.py#L36) | function | src\smart_core_assistant_painel\app\evolution_sync\services\message_buffer.py:36 |
| [`get_config`](src\smart_core_assistant_painel\modules\services\config\context.py#L73) | function | src\smart_core_assistant_painel\modules\services\config\context.py:73 |
| [`get_config_or_default`](src\smart_core_assistant_painel\modules\services\config\context.py#L88) | function | src\smart_core_assistant_painel\modules\services\config\context.py:88 |
| [`get_core_settings`](scripts\temp\diagnostico_config.py#L201) | function | scripts\temp\diagnostico_config.py:201 |
| [`get_current_tenant`](src\smart_core_assistant_painel\app\tenants\middleware.py#L15) | function | src\smart_core_assistant_painel\app\tenants\middleware.py:15 |
| [`get_current_tenant_slug`](src\smart_core_assistant_painel\app\tenants\tenant_context.py#L4) | function | src\smart_core_assistant_painel\app\tenants\tenant_context.py:4 |
| [`get_docker_host`](scripts\docker_remoto\manager.py#L78) | function | scripts\docker_remoto\manager.py:78 |
| [`get_feature_initials`](scripts\automacao\new_feature_script.py#L32) | function | scripts\automacao\new_feature_script.py:32 |
| [`get_fernet`](src\smart_core_assistant_painel\app\tenants\utils\encryption.py#L9) | function | src\smart_core_assistant_painel\app\tenants\utils\encryption.py:9 |
| [`get_image_base64`](scripts\temp\generate_proposal_html.py#L15) | function | scripts\temp\generate_proposal_html.py:15 |
| [`get_priority_style`](scripts\temp\visualize_tasks.py#L76) | function | scripts\temp\visualize_tasks.py:76 |
| [`get_project_name`](scripts\automacao\new_feature_script.py#L17) | function | scripts\automacao\new_feature_script.py:17 |
| [`get_runtime_config_fields`](scripts\temp\diagnostico_config.py#L216) | function | scripts\temp\diagnostico_config.py:216 |
| [`get_status_style`](scripts\temp\visualize_tasks.py#L59) | function | scripts\temp\visualize_tasks.py:59 |
| [`get_user_input`](scripts\automacao\new_feature_script.py#L242) | function | scripts\automacao\new_feature_script.py:242 |
| [`health_check`](src\smart_core_assistant_painel\app\ui\core\views.py#L85) | function | src\smart_core_assistant_painel\app\ui\core\views.py:85 |
| [`HtmlStrError`](src\smart_core_assistant_painel\modules\ai_engine\utils\erros.py#L14) | class | src\smart_core_assistant_painel\modules\ai_engine\utils\erros.py:14 |
| [`inicializar_atendimento_por_contato`](src\smart_core_assistant_painel\app\ui\atendimentos\models.py#L1439) | function | src\smart_core_assistant_painel\app\ui\atendimentos\models.py:1439 |
| [`inicializar_atendimento_whatsapp`](src\smart_core_assistant_painel\app\ui\atendimentos\models.py#L1253) | function | src\smart_core_assistant_painel\app\ui\atendimentos\models.py:1253 |
| [`invite_user`](src\smart_core_assistant_painel\app\tenants\views\invites.py#L67) | function | src\smart_core_assistant_painel\app\tenants\views\invites.py:67 |
| [`LandingPageView`](src\smart_core_assistant_painel\app\ui\core\views.py#L101) | class | src\smart_core_assistant_painel\app\ui\core\views.py:101 |
| [`list_users`](src\smart_core_assistant_painel\app\tenants\views\invites.py#L17) | function | src\smart_core_assistant_painel\app\tenants\views\invites.py:17 |
| [`list_webhooks`](teste_debug\list_webhooks.py#L27) | function | teste_debug\list_webhooks.py:27 |
| [`LlmError`](src\smart_core_assistant_painel\modules\ai_engine\utils\erros.py#L25) | class | src\smart_core_assistant_painel\modules\ai_engine\utils\erros.py:25 |
| [`LlmParameters`](src\smart_core_assistant_painel\modules\ai_engine\utils\parameters.py#L87) | class | src\smart_core_assistant_painel\modules\ai_engine\utils\parameters.py:87 |
| [`load_env`](scripts\config_global\sync_coresettings.py#L27) | function | scripts\config_global\sync_coresettings.py:27 |
| [`load_env`](scripts\docker_remoto\manager.py#L65) | function | scripts\docker_remoto\manager.py:65 |
| [`load_env_file`](scripts\temp\migrar_remoto.py#L26) | function | scripts\temp\migrar_remoto.py:26 |
| [`load_env_file`](scripts\temp\loaddata_remoto.py#L28) | function | scripts\temp\loaddata_remoto.py:28 |
| [`load_records`](scripts\temp\seed_query_compose\seed_query_compose.py#L34) | function | scripts\temp\seed_query_compose\seed_query_compose.py:34 |
| [`load_remote_config`](scripts\temp\extrair_prompts_remote_config.py#L64) | function | scripts\temp\extrair_prompts_remote_config.py:64 |
| [`load_tasks`](scripts\temp\visualize_tasks.py#L11) | function | scripts\temp\visualize_tasks.py:11 |
| [`LoadDocumentConteudoParameters`](src\smart_core_assistant_painel\modules\ai_engine\utils\parameters.py#L65) | class | src\smart_core_assistant_painel\modules\ai_engine\utils\parameters.py:65 |
| [`LoadDocumentConteudoUseCase`](src\smart_core_assistant_painel\modules\ai_engine\features\load_document_conteudo\domain\usecase\load_document_conteudo_usecase.py#L18) | class | src\smart_core_assistant_painel\modules\ai_engine\features\load_document_conteudo\domain\usecase\load_document_conteudo_usecase.py:18 |
| [`LoadDocumentFileDatasource`](src\smart_core_assistant_painel\modules\ai_engine\features\load_document_file\datasource\load_document_file_datasource.py#L17) | class | src\smart_core_assistant_painel\modules\ai_engine\features\load_document_file\datasource\load_document_file_datasource.py:17 |
| [`LoadDocumentFileParameters`](src\smart_core_assistant_painel\modules\ai_engine\utils\parameters.py#L42) | class | src\smart_core_assistant_painel\modules\ai_engine\utils\parameters.py:42 |
| [`LoadDocumentFileUseCase`](src\smart_core_assistant_painel\modules\ai_engine\features\load_document_file\domain\usecase\load_document_file_usecase.py#L18) | class | src\smart_core_assistant_painel\modules\ai_engine\features\load_document_file\domain\usecase\load_document_file_usecase.py:18 |
| [`LoadMensageDataUseCase`](src\smart_core_assistant_painel\modules\ai_engine\features\load_mensage_data\domain\usecase\load_mensage_data_usecase.py#L21) | class | src\smart_core_assistant_painel\modules\ai_engine\features\load_mensage_data\domain\usecase\load_mensage_data_usecase.py:21 |
| [`login`](src\smart_core_assistant_painel\app\ui\usuarios\views.py#L76) | function | src\smart_core_assistant_painel\app\ui\usuarios\views.py:76 |
| [`logout_view`](src\smart_core_assistant_painel\app\ui\usuarios\views.py#L134) | function | src\smart_core_assistant_painel\app\ui\usuarios\views.py:134 |
| [`main`](teste_debug\update_task_32.py#L128) | function | teste_debug\update_task_32.py:128 |
| [`main`](teste_debug\list_webhooks.py#L52) | function | teste_debug\list_webhooks.py:52 |
| [`main`](scripts\config_global\sync_coresettings.py#L157) | function | scripts\config_global\sync_coresettings.py:157 |
| [`main`](scripts\temp\visualize_tasks.py#L95) | function | scripts\temp\visualize_tasks.py:95 |
| [`main`](scripts\temp\migrar_remoto.py#L162) | function | scripts\temp\migrar_remoto.py:162 |
| [`main`](scripts\temp\loaddata_remoto.py#L225) | function | scripts\temp\loaddata_remoto.py:225 |
| [`main`](scripts\temp\extrair_prompts_remote_config.py#L143) | function | scripts\temp\extrair_prompts_remote_config.py:143 |
| [`main`](scripts\temp\diagnostico_config.py#L394) | function | scripts\temp\diagnostico_config.py:394 |
| [`main`](scripts\docker_remoto\manager.py#L154) | function | scripts\docker_remoto\manager.py:154 |
| [`main`](scripts\automacao\new_feature_script.py#L452) | function | scripts\automacao\new_feature_script.py:452 |
| [`main`](src\smart_core_assistant_painel\main.py#L72) | function | src\smart_core_assistant_painel\main.py:72 |
| [`main`](scripts\temp\trello\ngrok_trello.py#L14) | function | scripts\temp\trello\ngrok_trello.py:14 |
| [`main`](scripts\temp\seed_query_compose\seed_query_compose.py#L47) | function | scripts\temp\seed_query_compose\seed_query_compose.py:47 |
| [`main`](scripts\temp\database_reset\reset_database.py#L38) | function | scripts\temp\database_reset\reset_database.py:38 |
| [`markdown_format`](src\smart_core_assistant_painel\app\ui\treinamento\templatetags\markdown_extras.py#L11) | function | src\smart_core_assistant_painel\app\ui\treinamento\templatetags\markdown_extras.py:11 |
| [`MemberSyncService`](src\smart_core_assistant_painel\app\trello_sync\services\member_sync_service.py#L25) | class | src\smart_core_assistant_painel\app\trello_sync\services\member_sync_service.py:25 |
| [`Mensagem`](src\smart_core_assistant_painel\app\ui\atendimentos\models.py#L996) | class | src\smart_core_assistant_painel\app\ui\atendimentos\models.py:996 |
| [`mensagem_created_update_trello_card`](src\smart_core_assistant_painel\app\trello_sync\signals.py#L564) | function | src\smart_core_assistant_painel\app\trello_sync\signals.py:564 |
| [`MensagemAdmin`](src\smart_core_assistant_painel\app\ui\atendimentos\admin.py#L564) | class | src\smart_core_assistant_painel\app\ui\atendimentos\admin.py:564 |
| [`MensagemInline`](src\smart_core_assistant_painel\app\ui\atendimentos\admin.py#L25) | class | src\smart_core_assistant_painel\app\ui\atendimentos\admin.py:25 |
| [`MessageAnalyzer`](src\smart_core_assistant_painel\app\ui\atendimentos\services\message_analyzer.py#L24) | class | src\smart_core_assistant_painel\app\ui\atendimentos\services\message_analyzer.py:24 |
| [`MessageAnalyzerInterface`](src\smart_core_assistant_painel\app\ui\atendimentos\services\interfaces.py#L22) | class | src\smart_core_assistant_painel\app\ui\atendimentos\services\interfaces.py:22 |
| [`MessageData`](src\smart_core_assistant_painel\modules\ai_engine\features\load_mensage_data\domain\model\message_data.py#L15) | class | src\smart_core_assistant_painel\modules\ai_engine\features\load_mensage_data\domain\model\message_data.py:15 |
| [`Migration`](src\smart_core_assistant_painel\app\trello_sync\migrations\0001_initial.py#L7) | class | src\smart_core_assistant_painel\app\trello_sync\migrations\0001_initial.py:7 |
| [`Migration`](src\smart_core_assistant_painel\app\tenants\migrations\0002_tenant_onboarding_step_tenantconfig_brand_name_and_more.py#L6) | class | src\smart_core_assistant_painel\app\tenants\migrations\0002_tenant_onboarding_step_tenantconfig_brand_name_and_more.py:6 |
| [`Migration`](src\smart_core_assistant_painel\app\tenants\migrations\0001_initial.py#L9) | class | src\smart_core_assistant_painel\app\tenants\migrations\0001_initial.py:9 |
| [`Migration`](src\smart_core_assistant_painel\app\evolution_sync\migrations\0001_initial.py#L7) | class | src\smart_core_assistant_painel\app\evolution_sync\migrations\0001_initial.py:7 |
| [`Migration`](src\smart_core_assistant_painel\app\settings_manager\migrations\0001_initial.py#L6) | class | src\smart_core_assistant_painel\app\settings_manager\migrations\0001_initial.py:6 |
| [`Migration`](src\smart_core_assistant_painel\app\ui\treinamento\migrations\0001_initial.py#L10) | class | src\smart_core_assistant_painel\app\ui\treinamento\migrations\0001_initial.py:10 |
| [`Migration`](src\smart_core_assistant_painel\app\ui\operacional\migrations\0001_initial.py#L9) | class | src\smart_core_assistant_painel\app\ui\operacional\migrations\0001_initial.py:9 |
| [`Migration`](src\smart_core_assistant_painel\app\ui\atendimentos\migrations\0001_initial.py#L7) | class | src\smart_core_assistant_painel\app\ui\atendimentos\migrations\0001_initial.py:7 |
| [`Migration`](src\smart_core_assistant_painel\app\ui\clientes\migrations\0001_initial.py#L7) | class | src\smart_core_assistant_painel\app\ui\clientes\migrations\0001_initial.py:7 |
| [`mock_atendente`](src\smart_core_assistant_painel\app\ui\atendimentos\tests\test_models.py#L90) | function | src\smart_core_assistant_painel\app\ui\atendimentos\tests\test_models.py:90 |
| [`mock_atendimento`](src\smart_core_assistant_painel\app\ui\atendimentos\tests\services\test_bot_rules_engine.py#L23) | function | src\smart_core_assistant_painel\app\ui\atendimentos\tests\services\test_bot_rules_engine.py:23 |
| [`mock_atendimento_instance`](src\smart_core_assistant_painel\app\ui\atendimentos\tests\services\test_attendance_structure_manager.py#L24) | function | src\smart_core_assistant_painel\app\ui\atendimentos\tests\services\test_attendance_structure_manager.py:24 |
| [`mock_clickup_department_provision`](tests\conftest.py#L51) | function | tests\conftest.py:51 |
| [`mock_contato`](src\smart_core_assistant_painel\app\ui\atendimentos\tests\test_models.py#L80) | function | src\smart_core_assistant_painel\app\ui\atendimentos\tests\test_models.py:80 |
| [`mock_departamento`](src\smart_core_assistant_painel\app\ui\atendimentos\tests\test_models.py#L30) | function | src\smart_core_assistant_painel\app\ui\atendimentos\tests\test_models.py:30 |
| [`mock_django_q_async_task`](tests\conftest.py#L80) | function | tests\conftest.py:80 |
| [`mock_envelope`](src\smart_core_assistant_painel\app\evolution_sync\tests\services\test_webhook.py#L22) | function | src\smart_core_assistant_painel\app\evolution_sync\tests\services\test_webhook.py:22 |
| [`mock_etapa_atendimento`](src\smart_core_assistant_painel\app\ui\atendimentos\tests\test_models.py#L65) | function | src\smart_core_assistant_painel\app\ui\atendimentos\tests\test_models.py:65 |
| [`mock_etapa_fila`](src\smart_core_assistant_painel\app\ui\atendimentos\tests\test_models.py#L50) | function | src\smart_core_assistant_painel\app\ui\atendimentos\tests\test_models.py:50 |
| [`mock_firebase_admin`](tests\modules\services\features\set_environ_remote\datasource\test_set_environ_remote_firebase_datasource.py#L19) | function | tests\modules\services\features\set_environ_remote\datasource\test_set_environ_remote_firebase_datasource.py:19 |
| [`mock_fluxo`](src\smart_core_assistant_painel\app\ui\atendimentos\tests\test_models.py#L39) | function | src\smart_core_assistant_painel\app\ui\atendimentos\tests\test_models.py:39 |
| [`mock_message`](src\smart_core_assistant_painel\app\ui\atendimentos\tests\services\test_message_analyzer.py#L20) | function | src\smart_core_assistant_painel\app\ui\atendimentos\tests\services\test_message_analyzer.py:20 |
| [`mock_remote_config`](tests\modules\services\features\set_environ_remote\datasource\test_set_environ_remote_firebase_datasource.py#L24) | function | tests\modules\services\features\set_environ_remote\datasource\test_set_environ_remote_firebase_datasource.py:24 |
| [`mock_services`](src\smart_core_assistant_painel\app\ui\atendimentos\tests\services\test_attendance_orchestrator.py#L19) | function | src\smart_core_assistant_painel\app\ui\atendimentos\tests\services\test_attendance_orchestrator.py:19 |
| [`MockRequest`](src\smart_core_assistant_painel\app\ui\clientes\tests\test_clientes_admin.py#L13) | class | src\smart_core_assistant_painel\app\ui\clientes\tests\test_clientes_admin.py:13 |
| [`ModelsStrTests`](src\smart_core_assistant_painel\app\trello_sync\tests\test_models.py#L6) | class | src\smart_core_assistant_painel\app\trello_sync\tests\test_models.py:6 |
| [`MovimentoFluxo`](src\smart_core_assistant_painel\app\ui\atendimentos\models.py#L1122) | class | src\smart_core_assistant_painel\app\ui\atendimentos\models.py:1122 |
| [`MovimentoFluxoAdmin`](src\smart_core_assistant_painel\app\ui\operacional\admin.py#L404) | class | src\smart_core_assistant_painel\app\ui\operacional\admin.py:404 |
| [`normalize_evolution_webhook`](src\smart_core_assistant_painel\app\evolution_sync\normalizers.py#L8) | function | src\smart_core_assistant_painel\app\evolution_sync\normalizers.py:8 |
| [`normalize_evolution_webhook_batch`](src\smart_core_assistant_painel\app\evolution_sync\normalizers.py#L24) | function | src\smart_core_assistant_painel\app\evolution_sync\normalizers.py:24 |
| [`notify_expiring_subscriptions`](src\smart_core_assistant_painel\app\tenants\tasks.py#L38) | function | src\smart_core_assistant_painel\app\tenants\tasks.py:38 |
| [`NotionUnifiedDataService`](src\smart_core_assistant_painel\modules\services\features\unifield_data_services\datasource\notion_adapter.py#L30) | class | src\smart_core_assistant_painel\modules\services\features\unifield_data_services\datasource\notion_adapter.py:30 |
| [`OnboardingConfigForm`](src\smart_core_assistant_painel\app\tenants\forms\onboarding.py#L104) | class | src\smart_core_assistant_painel\app\tenants\forms\onboarding.py:104 |
| [`OnboardingSessionMixin`](src\smart_core_assistant_painel\app\tenants\views\onboarding.py#L13) | class | src\smart_core_assistant_painel\app\tenants\views\onboarding.py:13 |
| [`OperacionalConfig`](src\smart_core_assistant_painel\app\ui\operacional\apps.py#L5) | class | src\smart_core_assistant_painel\app\ui\operacional\apps.py:5 |
| [`orchestrator_instance`](src\smart_core_assistant_painel\app\ui\atendimentos\tests\services\test_attendance_orchestrator.py#L29) | function | src\smart_core_assistant_painel\app\ui\atendimentos\tests\services\test_attendance_orchestrator.py:29 |
| [`PaymentRecord`](src\smart_core_assistant_painel\app\tenants\models.py#L405) | class | src\smart_core_assistant_painel\app\tenants\models.py:405 |
| [`PaymentRecordAdmin`](src\smart_core_assistant_painel\app\tenants\admin.py#L300) | class | src\smart_core_assistant_painel\app\tenants\admin.py:300 |
| [`PaymentRecordInline`](src\smart_core_assistant_painel\app\tenants\admin.py#L18) | class | src\smart_core_assistant_painel\app\tenants\admin.py:18 |
| [`permissoes`](src\smart_core_assistant_painel\app\ui\usuarios\views.py#L144) | function | src\smart_core_assistant_painel\app\ui\usuarios\views.py:144 |
| [`Plan`](src\smart_core_assistant_painel\app\tenants\models.py#L311) | class | src\smart_core_assistant_painel\app\tenants\models.py:311 |
| [`PlanAdmin`](src\smart_core_assistant_painel\app\tenants\admin.py#L126) | class | src\smart_core_assistant_painel\app\tenants\admin.py:126 |
| [`PlanSelectionForm`](src\smart_core_assistant_painel\app\tenants\forms\onboarding.py#L92) | class | src\smart_core_assistant_painel\app\tenants\forms\onboarding.py:92 |
| [`pre_processamento`](src\smart_core_assistant_painel\app\ui\treinamento\views.py#L197) | function | src\smart_core_assistant_painel\app\ui\treinamento\views.py:197 |
| [`preencher_endereco_cep`](src\smart_core_assistant_painel\app\ui\clientes\signals.py#L11) | function | src\smart_core_assistant_painel\app\ui\clientes\signals.py:11 |
| [`print_diagnosis`](scripts\temp\diagnostico_config.py#L282) | function | scripts\temp\diagnostico_config.py:282 |
| [`print_header`](scripts\temp\migrar_remoto.py#L18) | function | scripts\temp\migrar_remoto.py:18 |
| [`print_header`](scripts\temp\loaddata_remoto.py#L20) | function | scripts\temp\loaddata_remoto.py:20 |
| [`print_header`](scripts\docker_remoto\manager.py#L57) | function | scripts\docker_remoto\manager.py:57 |
| [`process_contact_response_task`](src\smart_core_assistant_painel\app\ui\atendimentos\tasks.py#L15) | function | src\smart_core_assistant_painel\app\ui\atendimentos\tasks.py:15 |
| [`processar_mensagem_por_contato`](src\smart_core_assistant_painel\app\ui\atendimentos\models.py#L1571) | function | src\smart_core_assistant_painel\app\ui\atendimentos\models.py:1571 |
| [`processar_mensagem_whatsapp`](src\smart_core_assistant_painel\app\ui\atendimentos\models.py#L1363) | function | src\smart_core_assistant_painel\app\ui\atendimentos\models.py:1363 |
| [`processor`](src\smart_core_assistant_painel\app\evolution_sync\tests\services\test_webhook.py#L17) | function | src\smart_core_assistant_painel\app\evolution_sync\tests\services\test_webhook.py:17 |
| [`project_version`](src\smart_core_assistant_painel\app\ui\core\context_processors.py#L6) | function | src\smart_core_assistant_painel\app\ui\core\context_processors.py:6 |
| [`QueryCompose`](src\smart_core_assistant_painel\app\ui\treinamento\models.py#L246) | class | src\smart_core_assistant_painel\app\ui\treinamento\models.py:246 |
| [`QueryComposeAdmin`](src\smart_core_assistant_painel\app\ui\treinamento\admin.py#L328) | class | src\smart_core_assistant_painel\app\ui\treinamento\admin.py:328 |
| [`read_text`](scripts\automacao\new_feature_script.py#L56) | function | scripts\automacao\new_feature_script.py:56 |
| [`RegisterPaymentForm`](src\smart_core_assistant_painel\app\tenants\forms\legacy.py#L286) | class | src\smart_core_assistant_painel\app\tenants\forms\legacy.py:286 |
| [`RegisterPaymentView`](src\smart_core_assistant_painel\app\tenants\views\backoffice\register_payment.py#L10) | class | src\smart_core_assistant_painel\app\tenants\views\backoffice\register_payment.py:10 |
| [`RegisterTrelloWebhookView`](src\smart_core_assistant_painel\app\tenants\views\legacy_views.py#L535) | class | src\smart_core_assistant_painel\app\tenants\views\legacy_views.py:535 |
| [`remover_treinamento_ia_sync`](src\smart_core_assistant_painel\app\ui\treinamento\tasks.py#L154) | function | src\smart_core_assistant_painel\app\ui\treinamento\tasks.py:154 |
| [`resend_invite`](src\smart_core_assistant_painel\app\tenants\views\invites.py#L161) | function | src\smart_core_assistant_painel\app\tenants\views\invites.py:161 |
| [`RespostaBot`](src\smart_core_assistant_painel\modules\ai_engine\utils\types.py#L123) | class | src\smart_core_assistant_painel\modules\ai_engine\utils\types.py:123 |
| [`restore_action`](scripts\config_global\sync_coresettings.py#L106) | function | scripts\config_global\sync_coresettings.py:106 |
| [`run_command`](scripts\temp\database_reset\reset_database.py#L18) | function | scripts\temp\database_reset\reset_database.py:18 |
| [`run_compose`](scripts\docker_remoto\manager.py#L96) | function | scripts\docker_remoto\manager.py:96 |
| [`run_loaddata`](scripts\temp\loaddata_remoto.py#L124) | function | scripts\temp\loaddata_remoto.py:124 |
| [`run_migrations`](scripts\temp\migrar_remoto.py#L115) | function | scripts\temp\migrar_remoto.py:115 |
| [`run_ssh_psql`](scripts\config_global\sync_coresettings.py#L50) | function | scripts\config_global\sync_coresettings.py:50 |
| [`run_test`](teste_debug\verificar_trigger_feedback.py#L42) | function | teste_debug\verificar_trigger_feedback.py:42 |
| [`run_test`](teste_debug\verificar_feedback.py#L42) | function | teste_debug\verificar_feedback.py:42 |
| [`run_test`](teste_debug\test_flow_simulation.py#L166) | function | teste_debug\test_flow_simulation.py:166 |
| [`run_test`](teste_debug\test_expiration_task.py#L28) | function | teste_debug\test_expiration_task.py:28 |
| [`run_test`](teste_debug\reproduce_bug.py#L24) | function | teste_debug\reproduce_bug.py:24 |
| [`RunMigrationsView`](src\smart_core_assistant_painel\app\tenants\views\legacy_views.py#L324) | class | src\smart_core_assistant_painel\app\tenants\views\legacy_views.py:324 |
| [`RuntimeConfig`](src\smart_core_assistant_painel\modules\services\config\context.py#L7) | class | src\smart_core_assistant_painel\modules\services\config\context.py:7 |
| [`sanitize_name`](scripts\automacao\new_feature_script.py#L22) | function | scripts\automacao\new_feature_script.py:22 |
| [`sched_response_contact`](src\smart_core_assistant_painel\app\evolution_sync\services\message_buffer.py#L64) | function | src\smart_core_assistant_painel\app\evolution_sync\services\message_buffer.py:64 |
| [`SearchSimilarEmbeddingsParameters`](src\smart_core_assistant_painel\modules\ai_engine\utils\parameters.py#L211) | class | src\smart_core_assistant_painel\modules\ai_engine\utils\parameters.py:211 |
| [`service`](src\smart_core_assistant_painel\app\evolution_sync\tests\services\test_evolution_api.py#L12) | function | src\smart_core_assistant_painel\app\evolution_sync\tests\services\test_evolution_api.py:12 |
| [`ServiceHub`](src\smart_core_assistant_painel\modules\services\features\service_hub.py#L19) | class | src\smart_core_assistant_painel\modules\services\features\service_hub.py:19 |
| [`set_buffer_contact`](src\smart_core_assistant_painel\app\evolution_sync\services\message_buffer.py#L15) | function | src\smart_core_assistant_painel\app\evolution_sync\services\message_buffer.py:15 |
| [`set_config`](src\smart_core_assistant_painel\modules\services\config\context.py#L68) | function | src\smart_core_assistant_painel\modules\services\config\context.py:68 |
| [`set_current_tenant`](src\smart_core_assistant_painel\app\tenants\middleware.py#L20) | function | src\smart_core_assistant_painel\app\tenants\middleware.py:20 |
| [`SetEnvironRemoteError`](src\smart_core_assistant_painel\modules\services\utils\erros.py#L14) | class | src\smart_core_assistant_painel\modules\services\utils\erros.py:14 |
| [`SetEnvironRemoteParameters`](src\smart_core_assistant_painel\modules\services\utils\parameters.py#L19) | class | src\smart_core_assistant_painel\modules\services\utils\parameters.py:19 |
| [`SettingsManagerConfig`](src\smart_core_assistant_painel\app\settings_manager\apps.py#L4) | class | src\smart_core_assistant_painel\app\settings_manager\apps.py:4 |
| [`setup_environment`](scripts\temp\migrar_remoto.py#L46) | function | scripts\temp\migrar_remoto.py:46 |
| [`setup_environment`](scripts\temp\loaddata_remoto.py#L48) | function | scripts\temp\loaddata_remoto.py:48 |
| [`show_counts`](scripts\temp\loaddata_remoto.py#L185) | function | scripts\temp\loaddata_remoto.py:185 |
| [`signal_remover_treinamento_ia`](src\smart_core_assistant_painel\app\ui\treinamento\signals.py#L85) | function | src\smart_core_assistant_painel\app\ui\treinamento\signals.py:85 |
| [`signals_embeddings_documento`](src\smart_core_assistant_painel\app\ui\treinamento\signals.py#L39) | function | src\smart_core_assistant_painel\app\ui\treinamento\signals.py:39 |
| [`signals_embeddings_query_compose`](src\smart_core_assistant_painel\app\ui\treinamento\signals.py#L60) | function | src\smart_core_assistant_painel\app\ui\treinamento\signals.py:60 |
| [`signals_gerar_documentos_treinamento`](src\smart_core_assistant_painel\app\ui\treinamento\signals.py#L22) | function | src\smart_core_assistant_painel\app\ui\treinamento\signals.py:22 |
| [`start_app`](src\smart_core_assistant_painel\app\ui\manage.py#L10) | function | src\smart_core_assistant_painel\app\ui\manage.py:10 |
| [`start_initial_loading`](src\smart_core_assistant_painel\modules\initial_loading\start_initial_loading.py#L16) | function | src\smart_core_assistant_painel\modules\initial_loading\start_initial_loading.py:16 |
| [`start_services`](src\smart_core_assistant_painel\modules\services\start_services.py#L78) | function | src\smart_core_assistant_painel\modules\services\start_services.py:78 |
| [`StatusAtendimento`](src\smart_core_assistant_painel\app\ui\atendimentos\models.py#L24) | class | src\smart_core_assistant_painel\app\ui\atendimentos\models.py:24 |
| [`Step1TenantView`](src\smart_core_assistant_painel\app\tenants\views\onboarding.py#L29) | class | src\smart_core_assistant_painel\app\tenants\views\onboarding.py:29 |
| [`Step2PaymentView`](src\smart_core_assistant_painel\app\tenants\views\onboarding.py#L46) | class | src\smart_core_assistant_painel\app\tenants\views\onboarding.py:46 |
| [`Step3ConfigView`](src\smart_core_assistant_painel\app\tenants\views\onboarding.py#L71) | class | src\smart_core_assistant_painel\app\tenants\views\onboarding.py:71 |
| [`Step4ProvisionView`](src\smart_core_assistant_painel\app\tenants\views\onboarding.py#L90) | class | src\smart_core_assistant_painel\app\tenants\views\onboarding.py:90 |
| [`Subscription`](src\smart_core_assistant_painel\app\tenants\models.py#L336) | class | src\smart_core_assistant_painel\app\tenants\models.py:336 |
| [`SubscriptionAdmin`](src\smart_core_assistant_painel\app\tenants\admin.py#L324) | class | src\smart_core_assistant_painel\app\tenants\admin.py:324 |
| [`SubscriptionInline`](src\smart_core_assistant_painel\app\tenants\admin.py#L104) | class | src\smart_core_assistant_painel\app\tenants\admin.py:104 |
| [`task_atendente_invite`](src\smart_core_assistant_painel\app\trello_sync\tasks.py#L155) | function | src\smart_core_assistant_painel\app\trello_sync\tasks.py:155 |
| [`task_atendente_remove_member`](src\smart_core_assistant_painel\app\trello_sync\tasks.py#L173) | function | src\smart_core_assistant_painel\app\trello_sync\tasks.py:173 |
| [`task_atendimento_ensure_card`](src\smart_core_assistant_painel\app\trello_sync\tasks.py#L135) | function | src\smart_core_assistant_painel\app\trello_sync\tasks.py:135 |
| [`task_atendimento_move_to_etapa_list`](src\smart_core_assistant_painel\app\trello_sync\tasks.py#L208) | function | src\smart_core_assistant_painel\app\trello_sync\tasks.py:208 |
| [`task_atendimento_sync_card_members`](src\smart_core_assistant_painel\app\trello_sync\tasks.py#L184) | function | src\smart_core_assistant_painel\app\trello_sync\tasks.py:184 |
| [`task_atendimento_update_card_rich_content`](src\smart_core_assistant_painel\app\trello_sync\tasks.py#L229) | function | src\smart_core_assistant_painel\app\trello_sync\tasks.py:229 |
| [`task_etapa_archive_list`](src\smart_core_assistant_painel\app\trello_sync\tasks.py#L119) | function | src\smart_core_assistant_painel\app\trello_sync\tasks.py:119 |
| [`task_etapa_ensure_list`](src\smart_core_assistant_painel\app\trello_sync\tasks.py#L80) | function | src\smart_core_assistant_painel\app\trello_sync\tasks.py:80 |
| [`task_fluxo_archive_board`](src\smart_core_assistant_painel\app\trello_sync\tasks.py#L60) | function | src\smart_core_assistant_painel\app\trello_sync\tasks.py:60 |
| [`task_fluxo_ensure_board`](src\smart_core_assistant_painel\app\trello_sync\tasks.py#L43) | function | src\smart_core_assistant_painel\app\trello_sync\tasks.py:43 |
| [`task_gerar_documentos_treinamento`](src\smart_core_assistant_painel\app\ui\treinamento\tasks.py#L118) | function | src\smart_core_assistant_painel\app\ui\treinamento\tasks.py:118 |
| [`task_gerar_embedding_documento`](src\smart_core_assistant_painel\app\ui\treinamento\tasks.py#L40) | function | src\smart_core_assistant_painel\app\ui\treinamento\tasks.py:40 |
| [`task_gerar_embedding_query_compose`](src\smart_core_assistant_painel\app\ui\treinamento\tasks.py#L80) | function | src\smart_core_assistant_painel\app\ui\treinamento\tasks.py:80 |
| [`task_process_trello_card_move`](src\smart_core_assistant_painel\app\trello_sync\tasks.py#L269) | function | src\smart_core_assistant_painel\app\trello_sync\tasks.py:269 |
| [`task_process_trello_list_create`](src\smart_core_assistant_painel\app\trello_sync\tasks.py#L322) | function | src\smart_core_assistant_painel\app\trello_sync\tasks.py:322 |
| [`task_process_trello_list_update`](src\smart_core_assistant_painel\app\trello_sync\tasks.py#L383) | function | src\smart_core_assistant_painel\app\trello_sync\tasks.py:383 |
| [`task_reorder_lists_for_fluxo`](src\smart_core_assistant_painel\app\trello_sync\tasks.py#L101) | function | src\smart_core_assistant_painel\app\trello_sync\tasks.py:101 |
| [`task_trello_archive_card_by_external_id`](src\smart_core_assistant_painel\app\trello_sync\tasks.py#L250) | function | src\smart_core_assistant_painel\app\trello_sync\tasks.py:250 |
| [`Tenant`](src\smart_core_assistant_painel\app\tenants\models.py#L14) | class | src\smart_core_assistant_painel\app\tenants\models.py:14 |
| [`tenant_required`](src\smart_core_assistant_painel\app\tenants\api_mixins.py#L10) | function | src\smart_core_assistant_painel\app\tenants\api_mixins.py:10 |
| [`TenantAdmin`](src\smart_core_assistant_painel\app\tenants\admin.py#L139) | class | src\smart_core_assistant_painel\app\tenants\admin.py:139 |
| [`TenantAdminSite`](src\smart_core_assistant_painel\app\tenants\admin_client.py#L7) | class | src\smart_core_assistant_painel\app\tenants\admin_client.py:7 |
| [`TenantAppInstanceAdmin`](src\smart_core_assistant_painel\app\ui\operacional\tenant_admin.py#L45) | class | src\smart_core_assistant_painel\app\ui\operacional\tenant_admin.py:45 |
| [`TenantAtendenteAdmin`](src\smart_core_assistant_painel\app\ui\operacional\tenant_admin.py#L35) | class | src\smart_core_assistant_painel\app\ui\operacional\tenant_admin.py:35 |
| [`TenantAtendimentoAdmin`](src\smart_core_assistant_painel\app\ui\atendimentos\tenant_admin.py#L30) | class | src\smart_core_assistant_painel\app\ui\atendimentos\tenant_admin.py:30 |
| [`TenantClienteAdmin`](src\smart_core_assistant_painel\app\ui\clientes\tenant_admin.py#L42) | class | src\smart_core_assistant_painel\app\ui\clientes\tenant_admin.py:42 |
| [`TenantConfig`](src\smart_core_assistant_painel\app\tenants\models.py#L161) | class | src\smart_core_assistant_painel\app\tenants\models.py:161 |
| [`TenantConfigForm`](src\smart_core_assistant_painel\app\tenants\forms\legacy.py#L135) | class | src\smart_core_assistant_painel\app\tenants\forms\legacy.py:135 |
| [`TenantConfigInline`](src\smart_core_assistant_painel\app\tenants\admin.py#L76) | class | src\smart_core_assistant_painel\app\tenants\admin.py:76 |
| [`TenantConfigMiddleware`](src\smart_core_assistant_painel\app\tenants\middleware.py#L257) | class | src\smart_core_assistant_painel\app\tenants\middleware.py:257 |
| [`TenantContatoAdmin`](src\smart_core_assistant_painel\app\ui\clientes\tenant_admin.py#L24) | class | src\smart_core_assistant_painel\app\ui\clientes\tenant_admin.py:24 |
| [`TenantCreateMixin`](src\smart_core_assistant_painel\app\tenants\api_mixins.py#L54) | class | src\smart_core_assistant_painel\app\tenants\api_mixins.py:54 |
| [`TenantDatabase`](src\smart_core_assistant_painel\app\tenants\models.py#L47) | class | src\smart_core_assistant_painel\app\tenants\models.py:47 |
| [`TenantDatabaseForm`](src\smart_core_assistant_painel\app\tenants\forms\legacy.py#L238) | class | src\smart_core_assistant_painel\app\tenants\forms\legacy.py:238 |
| [`TenantDatabaseInline`](src\smart_core_assistant_painel\app\tenants\admin.py#L32) | class | src\smart_core_assistant_painel\app\tenants\admin.py:32 |
| [`TenantDatabaseRouter`](src\smart_core_assistant_painel\app\tenants\db_router.py#L31) | class | src\smart_core_assistant_painel\app\tenants\db_router.py:31 |
| [`TenantDepartamentoAdmin`](src\smart_core_assistant_painel\app\ui\operacional\tenant_admin.py#L23) | class | src\smart_core_assistant_painel\app\ui\operacional\tenant_admin.py:23 |
| [`TenantDocumentoAdmin`](src\smart_core_assistant_painel\app\ui\treinamento\tenant_admin.py#L44) | class | src\smart_core_assistant_painel\app\ui\treinamento\tenant_admin.py:44 |
| [`TenantEtapaFluxoAdmin`](src\smart_core_assistant_painel\app\ui\operacional\tenant_admin.py#L69) | class | src\smart_core_assistant_painel\app\ui\operacional\tenant_admin.py:69 |
| [`TenantEvolution`](src\smart_core_assistant_painel\app\tenants\models.py#L85) | class | src\smart_core_assistant_painel\app\tenants\models.py:85 |
| [`TenantEvolutionContactAdmin`](src\smart_core_assistant_painel\app\evolution_sync\tenant_admin.py#L45) | class | src\smart_core_assistant_painel\app\evolution_sync\tenant_admin.py:45 |
| [`TenantEvolutionForm`](src\smart_core_assistant_painel\app\tenants\forms\legacy.py#L56) | class | src\smart_core_assistant_painel\app\tenants\forms\legacy.py:56 |
| [`TenantEvolutionInline`](src\smart_core_assistant_painel\app\tenants\admin.py#L48) | class | src\smart_core_assistant_painel\app\tenants\admin.py:48 |
| [`TenantEvolutionInstanceAdmin`](src\smart_core_assistant_painel\app\evolution_sync\tenant_admin.py#L23) | class | src\smart_core_assistant_painel\app\evolution_sync\tenant_admin.py:23 |
| [`TenantFilterMixin`](src\smart_core_assistant_painel\app\tenants\admin_mixins.py#L80) | class | src\smart_core_assistant_painel\app\tenants\admin_mixins.py:80 |
| [`TenantFluxoAtendimentoAdmin`](src\smart_core_assistant_painel\app\ui\operacional\tenant_admin.py#L57) | class | src\smart_core_assistant_painel\app\ui\operacional\tenant_admin.py:57 |
| [`TenantForeignKeyValidator`](src\smart_core_assistant_painel\app\tenants\api_mixins.py#L65) | class | src\smart_core_assistant_painel\app\tenants\api_mixins.py:65 |
| [`TenantInvite`](src\smart_core_assistant_painel\app\tenants\models.py#L440) | class | src\smart_core_assistant_painel\app\tenants\models.py:440 |
| [`TenantMensagemAdmin`](src\smart_core_assistant_painel\app\ui\atendimentos\tenant_admin.py#L58) | class | src\smart_core_assistant_painel\app\ui\atendimentos\tenant_admin.py:58 |
| [`TenantMensagemInline`](src\smart_core_assistant_painel\app\ui\atendimentos\tenant_admin.py#L16) | class | src\smart_core_assistant_painel\app\ui\atendimentos\tenant_admin.py:16 |
| [`TenantMiddleware`](src\smart_core_assistant_painel\app\tenants\middleware.py#L31) | class | src\smart_core_assistant_painel\app\tenants\middleware.py:31 |
| [`TenantMigrationRunner`](src\smart_core_assistant_painel\app\tenants\services\connection_tester.py#L135) | class | src\smart_core_assistant_painel\app\tenants\services\connection_tester.py:135 |
| [`TenantModelAdminMixin`](src\smart_core_assistant_painel\app\tenants\mixins.py#L45) | class | src\smart_core_assistant_painel\app\tenants\mixins.py:45 |
| [`TenantModule`](src\smart_core_assistant_painel\app\tenants\permissions.py#L4) | class | src\smart_core_assistant_painel\app\tenants\permissions.py:4 |
| [`TenantMovimentoFluxoAdmin`](src\smart_core_assistant_painel\app\ui\operacional\tenant_admin.py#L81) | class | src\smart_core_assistant_painel\app\ui\operacional\tenant_admin.py:81 |
| [`TenantPermissionMixin`](src\smart_core_assistant_painel\app\tenants\admin_mixins.py#L14) | class | src\smart_core_assistant_painel\app\tenants\admin_mixins.py:14 |
| [`TenantProvisioningService`](src\smart_core_assistant_painel\app\tenants\services\provisioning.py#L9) | class | src\smart_core_assistant_painel\app\tenants\services\provisioning.py:9 |
| [`TenantQueryComposeAdmin`](src\smart_core_assistant_painel\app\ui\treinamento\tenant_admin.py#L55) | class | src\smart_core_assistant_painel\app\ui\treinamento\tenant_admin.py:55 |
| [`TenantQuerysetMixin`](src\smart_core_assistant_painel\app\tenants\api_mixins.py#L22) | class | src\smart_core_assistant_painel\app\tenants\api_mixins.py:22 |
| [`TenantRegistrationForm`](src\smart_core_assistant_painel\app\tenants\forms\onboarding.py#L12) | class | src\smart_core_assistant_painel\app\tenants\forms\onboarding.py:12 |
| [`TenantRoleType`](src\smart_core_assistant_painel\app\tenants\permissions.py#L22) | class | src\smart_core_assistant_painel\app\tenants\permissions.py:22 |
| [`TenantsConfig`](src\smart_core_assistant_painel\app\tenants\apps.py#L4) | class | src\smart_core_assistant_painel\app\tenants\apps.py:4 |
| [`TenantSignupForm`](src\smart_core_assistant_painel\app\tenants\forms\legacy.py#L19) | class | src\smart_core_assistant_painel\app\tenants\forms\legacy.py:19 |
| [`TenantSignupView`](src\smart_core_assistant_painel\app\tenants\views\legacy_views.py#L46) | class | src\smart_core_assistant_painel\app\tenants\views\legacy_views.py:46 |
| [`TenantTask`](src\smart_core_assistant_painel\app\tenants\celery.py#L5) | class | src\smart_core_assistant_painel\app\tenants\celery.py:5 |
| [`TenantTreinamentoAdmin`](src\smart_core_assistant_painel\app\ui\treinamento\tenant_admin.py#L20) | class | src\smart_core_assistant_painel\app\ui\treinamento\tenant_admin.py:20 |
| [`TenantTrello`](src\smart_core_assistant_painel\app\tenants\models.py#L111) | class | src\smart_core_assistant_painel\app\tenants\models.py:111 |
| [`TenantTrelloBoardAdmin`](src\smart_core_assistant_painel\app\trello_sync\tenant_admin.py#L26) | class | src\smart_core_assistant_painel\app\trello_sync\tenant_admin.py:26 |
| [`TenantTrelloCardAdmin`](src\smart_core_assistant_painel\app\trello_sync\tenant_admin.py#L48) | class | src\smart_core_assistant_painel\app\trello_sync\tenant_admin.py:48 |
| [`TenantTrelloForm`](src\smart_core_assistant_painel\app\tenants\forms\legacy.py#L83) | class | src\smart_core_assistant_painel\app\tenants\forms\legacy.py:83 |
| [`TenantTrelloInline`](src\smart_core_assistant_painel\app\tenants\admin.py#L61) | class | src\smart_core_assistant_painel\app\tenants\admin.py:61 |
| [`TenantTrelloListAdmin`](src\smart_core_assistant_painel\app\trello_sync\tenant_admin.py#L37) | class | src\smart_core_assistant_painel\app\trello_sync\tenant_admin.py:37 |
| [`TenantTrelloMemberAdmin`](src\smart_core_assistant_painel\app\trello_sync\tenant_admin.py#L65) | class | src\smart_core_assistant_painel\app\trello_sync\tenant_admin.py:65 |
| [`TenantTrelloWebhookEventAdmin`](src\smart_core_assistant_painel\app\trello_sync\tenant_admin.py#L75) | class | src\smart_core_assistant_painel\app\trello_sync\tenant_admin.py:75 |
| [`TenantUser`](src\smart_core_assistant_painel\app\tenants\models.py#L493) | class | src\smart_core_assistant_painel\app\tenants\models.py:493 |
| [`TenantWhiteListAdmin`](src\smart_core_assistant_painel\app\evolution_sync\tenant_admin.py#L69) | class | src\smart_core_assistant_painel\app\evolution_sync\tenant_admin.py:69 |
| [`test_connectivity`](scripts\temp\migrar_remoto.py#L85) | function | scripts\temp\migrar_remoto.py:85 |
| [`test_connectivity`](scripts\temp\loaddata_remoto.py#L83) | function | scripts\temp\loaddata_remoto.py:83 |
| [`test_default_etapas_created_for_atendimento`](src\smart_core_assistant_painel\app\ui\operacional\tests\test_signals.py#L21) | function | src\smart_core_assistant_painel\app\ui\operacional\tests\test_signals.py:21 |
| [`test_evolution_contact_data_from_dict`](src\smart_core_assistant_painel\app\evolution_sync\tests\domain\test_schemas.py#L59) | function | src\smart_core_assistant_painel\app\evolution_sync\tests\domain\test_schemas.py:59 |
| [`test_evolution_contact_data_from_dict_lid`](src\smart_core_assistant_painel\app\evolution_sync\tests\domain\test_schemas.py#L73) | function | src\smart_core_assistant_painel\app\evolution_sync\tests\domain\test_schemas.py:73 |
| [`test_evolution_contact_data_is_group`](src\smart_core_assistant_painel\app\evolution_sync\tests\domain\test_schemas.py#L221) | function | src\smart_core_assistant_painel\app\evolution_sync\tests\domain\test_schemas.py:221 |
| [`test_evolution_contact_data_to_dict`](src\smart_core_assistant_painel\app\evolution_sync\tests\domain\test_schemas.py#L86) | function | src\smart_core_assistant_painel\app\evolution_sync\tests\domain\test_schemas.py:86 |
| [`test_evolution_message_data_from_dict_conversation`](src\smart_core_assistant_painel\app\evolution_sync\tests\domain\test_schemas.py#L9) | function | src\smart_core_assistant_painel\app\evolution_sync\tests\domain\test_schemas.py:9 |
| [`test_evolution_message_data_from_dict_extended_text`](src\smart_core_assistant_painel\app\evolution_sync\tests\domain\test_schemas.py#L29) | function | src\smart_core_assistant_painel\app\evolution_sync\tests\domain\test_schemas.py:29 |
| [`test_evolution_message_data_to_dict`](src\smart_core_assistant_painel\app\evolution_sync\tests\domain\test_schemas.py#L43) | function | src\smart_core_assistant_painel\app\evolution_sync\tests\domain\test_schemas.py:43 |
| [`test_evolution_metadata_optimization`](teste_debug\verify_evolution_metadata.py#L36) | function | teste_debug\verify_evolution_metadata.py:36 |
| [`test_evolution_profile_data_from_dict`](src\smart_core_assistant_painel\app\evolution_sync\tests\domain\test_schemas.py#L99) | function | src\smart_core_assistant_painel\app\evolution_sync\tests\domain\test_schemas.py:99 |
| [`test_evolution_profile_data_to_dict`](src\smart_core_assistant_painel\app\evolution_sync\tests\domain\test_schemas.py#L107) | function | src\smart_core_assistant_painel\app\evolution_sync\tests\domain\test_schemas.py:107 |
| [`test_evolution_webhook_envelope_from_dict`](src\smart_core_assistant_painel\app\evolution_sync\tests\domain\test_schemas.py#L115) | function | src\smart_core_assistant_painel\app\evolution_sync\tests\domain\test_schemas.py:115 |
| [`test_evolution_webhook_envelope_from_dict_batch`](src\smart_core_assistant_painel\app\evolution_sync\tests\domain\test_schemas.py#L182) | function | src\smart_core_assistant_painel\app\evolution_sync\tests\domain\test_schemas.py:182 |
| [`test_evolution_webhook_envelope_from_dict_single`](src\smart_core_assistant_painel\app\evolution_sync\tests\domain\test_schemas.py#L145) | function | src\smart_core_assistant_painel\app\evolution_sync\tests\domain\test_schemas.py:145 |
| [`test_evolution_webhook_envelope_from_dict_single_with_list_data`](src\smart_core_assistant_painel\app\evolution_sync\tests\domain\test_schemas.py#L160) | function | src\smart_core_assistant_painel\app\evolution_sync\tests\domain\test_schemas.py:160 |
| [`test_evolution_webhook_envelope_to_dict`](src\smart_core_assistant_painel\app\evolution_sync\tests\domain\test_schemas.py#L204) | function | src\smart_core_assistant_painel\app\evolution_sync\tests\domain\test_schemas.py:204 |
| [`test_normalize_evolution_webhook_batch_with_list`](src\smart_core_assistant_painel\app\evolution_sync\tests\test_normalizers.py#L45) | function | src\smart_core_assistant_painel\app\evolution_sync\tests\test_normalizers.py:45 |
| [`test_normalize_evolution_webhook_single_dict`](src\smart_core_assistant_painel\app\evolution_sync\tests\test_normalizers.py#L17) | function | src\smart_core_assistant_painel\app\evolution_sync\tests\test_normalizers.py:17 |
| [`test_on_message_saved_already_responded`](src\smart_core_assistant_painel\app\evolution_sync\tests\test_signals.py#L58) | function | src\smart_core_assistant_painel\app\evolution_sync\tests\test_signals.py:58 |
| [`test_on_message_saved_not_created`](src\smart_core_assistant_painel\app\evolution_sync\tests\test_signals.py#L49) | function | src\smart_core_assistant_painel\app\evolution_sync\tests\test_signals.py:49 |
| [`test_on_message_saved_success`](src\smart_core_assistant_painel\app\evolution_sync\tests\test_signals.py#L14) | function | src\smart_core_assistant_painel\app\evolution_sync\tests\test_signals.py:14 |
| [`test_process_webhook_filters_group_messages`](src\smart_core_assistant_painel\app\evolution_sync\tests\services\test_webhook.py#L109) | function | src\smart_core_assistant_painel\app\evolution_sync\tests\services\test_webhook.py:109 |
| [`test_process_webhook_ignored_from_me`](src\smart_core_assistant_painel\app\evolution_sync\tests\services\test_webhook.py#L98) | function | src\smart_core_assistant_painel\app\evolution_sync\tests\services\test_webhook.py:98 |
| [`test_process_webhook_success`](src\smart_core_assistant_painel\app\evolution_sync\tests\services\test_webhook.py#L47) | function | src\smart_core_assistant_painel\app\evolution_sync\tests\services\test_webhook.py:47 |
| [`test_pydantic_model_docstring_generated_from_jsons`](tests\modules\ai_engine\features\analise_previa_mensagem\datasource\langchain_pydantic\test_pydantic_model_factory_docs.py#L9) | function | tests\modules\ai_engine\features\analise_previa_mensagem\datasource\langchain_pydantic\test_pydantic_model_factory_docs.py:9 |
| [`test_pydantic_model_schema_unchanged_no_confidence`](tests\modules\ai_engine\features\analise_previa_mensagem\datasource\langchain_pydantic\test_pydantic_model_factory_docs.py#L77) | function | tests\modules\ai_engine\features\analise_previa_mensagem\datasource\langchain_pydantic\test_pydantic_model_factory_docs.py:77 |
| [`test_send_message_failure`](src\smart_core_assistant_painel\app\evolution_sync\tests\services\test_evolution_api.py#L81) | function | src\smart_core_assistant_painel\app\evolution_sync\tests\services\test_evolution_api.py:81 |
| [`test_send_message_success`](src\smart_core_assistant_painel\app\evolution_sync\tests\services\test_evolution_api.py#L41) | function | src\smart_core_assistant_painel\app\evolution_sync\tests\services\test_evolution_api.py:41 |
| [`test_send_request_success`](src\smart_core_assistant_painel\app\evolution_sync\tests\services\test_evolution_api.py#L17) | function | src\smart_core_assistant_painel\app\evolution_sync\tests\services\test_evolution_api.py:17 |
| [`test_signal_transferencia_humano`](teste_debug\test_signal_transferencia.py#L19) | function | teste_debug\test_signal_transferencia.py:19 |
| [`test_sync_status_from_etapa_logica`](teste_debug\test_trello_webhook_logic.py#L17) | function | teste_debug\test_trello_webhook_logic.py:17 |
| [`test_sync_status_ignores_finalizacao`](teste_debug\test_trello_webhook_logic.py#L41) | function | teste_debug\test_trello_webhook_logic.py:41 |
| [`test_ticket_sync_service_import_check`](teste_debug\verificar_correcoes_task_28.py#L90) | function | teste_debug\verificar_correcoes_task_28.py:90 |
| [`test_verify_member_sync_service_method`](teste_debug\verificar_correcoes_task_28.py#L66) | function | teste_debug\verificar_correcoes_task_28.py:66 |
| [`test_verify_trello_adapter_log_correction`](teste_debug\verificar_correcoes_task_28.py#L27) | function | teste_debug\verificar_correcoes_task_28.py:27 |
| [`test_webhook_view_invalid_json`](src\smart_core_assistant_painel\app\evolution_sync\tests\test_views.py#L52) | function | src\smart_core_assistant_painel\app\evolution_sync\tests\test_views.py:52 |
| [`test_webhook_view_invalid_method`](src\smart_core_assistant_painel\app\evolution_sync\tests\test_views.py#L44) | function | src\smart_core_assistant_painel\app\evolution_sync\tests\test_views.py:44 |
| [`test_webhook_view_success`](src\smart_core_assistant_painel\app\evolution_sync\tests\test_views.py#L19) | function | src\smart_core_assistant_painel\app\evolution_sync\tests\test_views.py:19 |
| [`TestAnaliseConteudoLangchainDatasource`](tests\modules\ai_engine\features\analise_conteudo\datasource\test_analise_conteudo_langchain_datasource.py#L16) | class | tests\modules\ai_engine\features\analise_conteudo\datasource\test_analise_conteudo_langchain_datasource.py:16 |
| [`TestAnaliseConteudoUseCase`](tests\modules\ai_engine\features\analise_conteudo\domain\usecase\test_analise_conteudo_usecase.py#L18) | class | tests\modules\ai_engine\features\analise_conteudo\domain\usecase\test_analise_conteudo_usecase.py:18 |
| [`TestAnalisePreviaLangchainDatasource`](tests\modules\ai_engine\features\analise_previa_mensagem\datasource\analise_previa_langchain\test_analise_previa_langchain_datasource.py#L20) | class | tests\modules\ai_engine\features\analise_previa_mensagem\datasource\analise_previa_langchain\test_analise_previa_langchain_datasource.py:20 |
| [`TestAnalisePreviaMensagemLangchain`](tests\modules\ai_engine\features\analise_previa_mensagem\datasource\langchain_pydantic\test_analise_previa_mensagem_langchain.py#L12) | class | tests\modules\ai_engine\features\analise_previa_mensagem\datasource\langchain_pydantic\test_analise_previa_mensagem_langchain.py:12 |
| [`TestAnalisePreviaMensagemLangchainDatasource`](tests\modules\ai_engine\features\analise_previa_mensagem\datasource\langchain_pydantic\test_analise_previa_mensagem_langchain_datasource.py#L18) | class | tests\modules\ai_engine\features\analise_previa_mensagem\datasource\langchain_pydantic\test_analise_previa_mensagem_langchain_datasource.py:18 |
| [`TestAnalisePreviaMensagemUsecase`](tests\modules\ai_engine\features\analise_previa_mensagem\domain\usecase\test_analise_previa_mensagem_usecase.py#L23) | class | tests\modules\ai_engine\features\analise_previa_mensagem\domain\usecase\test_analise_previa_mensagem_usecase.py:23 |
| [`TestAtendimentoFunctions`](src\smart_core_assistant_painel\app\ui\atendimentos\tests\test_models.py#L410) | class | src\smart_core_assistant_painel\app\ui\atendimentos\tests\test_models.py:410 |
| [`TestAtendimentoModel`](src\smart_core_assistant_painel\app\ui\atendimentos\tests\test_models.py#L109) | class | src\smart_core_assistant_painel\app\ui\atendimentos\tests\test_models.py:109 |
| [`TestAttendanceOrchestrator`](src\smart_core_assistant_painel\app\ui\atendimentos\tests\services\test_attendance_orchestrator.py#L40) | class | src\smart_core_assistant_painel\app\ui\atendimentos\tests\services\test_attendance_orchestrator.py:40 |
| [`TestAttendanceStructureManager`](src\smart_core_assistant_painel\app\ui\atendimentos\tests\services\test_attendance_structure_manager.py#L38) | class | src\smart_core_assistant_painel\app\ui\atendimentos\tests\services\test_attendance_structure_manager.py:38 |
| [`TestBotRulesEngine`](src\smart_core_assistant_painel\app\ui\atendimentos\tests\services\test_bot_rules_engine.py#L37) | class | src\smart_core_assistant_painel\app\ui\atendimentos\tests\services\test_bot_rules_engine.py:37 |
| [`TestBotRulesEngineFlag`](src\smart_core_assistant_painel\app\ui\atendimentos\tests\services\test_bot_rules_engine_flag.py#L20) | class | src\smart_core_assistant_painel\app\ui\atendimentos\tests\services\test_bot_rules_engine_flag.py:20 |
| [`TestClicupUnifiedDataService`](tests\modules\services\features\unifield_data_services\datasource\test_clicup_adapter.py#L16) | class | tests\modules\services\features\unifield_data_services\datasource\test_clicup_adapter.py:16 |
| [`TestClientesAppUrls`](src\smart_core_assistant_painel\app\ui\clientes\tests\test_clientes_urls.py#L6) | class | src\smart_core_assistant_painel\app\ui\clientes\tests\test_clientes_urls.py:6 |
| [`TestClientesAppViews`](src\smart_core_assistant_painel\app\ui\clientes\tests\test_clientes_views.py#L6) | class | src\smart_core_assistant_painel\app\ui\clientes\tests\test_clientes_views.py:6 |
| [`TestClientesCliente`](src\smart_core_assistant_painel\app\ui\clientes\tests\test_clientes_models.py#L34) | class | src\smart_core_assistant_painel\app\ui\clientes\tests\test_clientes_models.py:34 |
| [`TestClientesContato`](src\smart_core_assistant_painel\app\ui\clientes\tests\test_clientes_models.py#L8) | class | src\smart_core_assistant_painel\app\ui\clientes\tests\test_clientes_models.py:8 |
| [`TestClientesContatoAdmin`](src\smart_core_assistant_painel\app\ui\clientes\tests\test_clientes_admin.py#L20) | class | src\smart_core_assistant_painel\app\ui\clientes\tests\test_clientes_admin.py:20 |
| [`TestClientesContatoForm`](src\smart_core_assistant_painel\app\ui\clientes\tests\test_clientes_forms.py#L30) | class | src\smart_core_assistant_painel\app\ui\clientes\tests\test_clientes_forms.py:30 |
| [`TestCommunicationRules`](src\smart_core_assistant_painel\app\evolution_sync\tests\test_communication_rules.py#L18) | class | src\smart_core_assistant_painel\app\evolution_sync\tests\test_communication_rules.py:18 |
| [`TestConnectionView`](src\smart_core_assistant_painel\app\tenants\views\legacy_views.py#L274) | class | src\smart_core_assistant_painel\app\tenants\views\legacy_views.py:274 |
| [`TestCreateDynamicPydanticModel`](tests\modules\ai_engine\features\analise_previa_mensagem\datasource\langchain_pydantic\test_pydantic_model_factory.py#L208) | class | tests\modules\ai_engine\features\analise_previa_mensagem\datasource\langchain_pydantic\test_pydantic_model_factory.py:208 |
| [`TestEvolutionWebhookFlow`](src\smart_core_assistant_painel\app\evolution_sync\tests\test_webhook_flow.py#L18) | class | src\smart_core_assistant_painel\app\evolution_sync\tests\test_webhook_flow.py:18 |
| [`TestFeaturesCompose`](tests\modules\ai_engine\features\test_features_compose.py#L17) | class | tests\modules\ai_engine\features\test_features_compose.py:17 |
| [`TestFirebaseInitUseCase`](tests\modules\initial_loading\features\firebase_init\domain\usecase\test_firebase_init_usecase.py#L18) | class | tests\modules\initial_loading\features\firebase_init\domain\usecase\test_firebase_init_usecase.py:18 |
| [`TestGenerateEmbeddingsLangchainDatasource`](tests\modules\ai_engine\features\generate_embeddings\datasource\test_generate_embeddings_langchain_datasource.py#L17) | class | tests\modules\ai_engine\features\generate_embeddings\datasource\test_generate_embeddings_langchain_datasource.py:17 |
| [`TestInMemoryUnifiedDataService`](tests\modules\services\features\unifield_data_services\datasource\test_unifield_data_services_datasource.py#L65) | class | tests\modules\services\features\unifield_data_services\datasource\test_unifield_data_services_datasource.py:65 |
| [`TestLoadDocumentConteudoUseCase`](tests\modules\ai_engine\features\load_document_conteudo\domain\usecase\test_load_document_conteudo_usecase.py#L20) | class | tests\modules\ai_engine\features\load_document_conteudo\domain\usecase\test_load_document_conteudo_usecase.py:20 |
| [`TestLoadDocumentFileDatasource`](tests\modules\ai_engine\features\load_document_file\datasource\test_load_document_file_datasource.py#L19) | class | tests\modules\ai_engine\features\load_document_file\datasource\test_load_document_file_datasource.py:19 |
| [`TestLoadDocumentFileUseCase`](tests\modules\ai_engine\features\load_document_file\domain\usecase\test_load_document_file_usecase.py#L20) | class | tests\modules\ai_engine\features\load_document_file\domain\usecase\test_load_document_file_usecase.py:20 |
| [`TestLoadMensageDataUseCase`](tests\modules\ai_engine\features\load_mensage_data\domain\usecase\test_load_mensage_data_usecase.py#L15) | class | tests\modules\ai_engine\features\load_mensage_data\domain\usecase\test_load_mensage_data_usecase.py:15 |
| [`TestMensagemModel`](src\smart_core_assistant_painel\app\ui\atendimentos\tests\test_models.py#L365) | class | src\smart_core_assistant_painel\app\ui\atendimentos\tests\test_models.py:365 |
| [`TestMessageAnalyzer`](src\smart_core_assistant_painel\app\ui\atendimentos\tests\services\test_message_analyzer.py#L56) | class | src\smart_core_assistant_painel\app\ui\atendimentos\tests\services\test_message_analyzer.py:56 |
| [`TestOperacionalAppUrls`](src\smart_core_assistant_painel\app\ui\operacional\tests\test_operacional_urls.py#L6) | class | src\smart_core_assistant_painel\app\ui\operacional\tests\test_operacional_urls.py:6 |
| [`TestOperacionalAppViews`](src\smart_core_assistant_painel\app\ui\operacional\tests\test_operacional_views.py#L6) | class | src\smart_core_assistant_painel\app\ui\operacional\tests\test_operacional_views.py:6 |
| [`TestPreProcessamentoViews`](src\smart_core_assistant_painel\app\ui\treinamento\tests\test_treinamento_views.py#L257) | class | src\smart_core_assistant_painel\app\ui\treinamento\tests\test_treinamento_views.py:257 |
| [`TestPydanticModelFactory`](tests\modules\ai_engine\features\analise_previa_mensagem\datasource\langchain_pydantic\test_pydantic_model_factory.py#L14) | class | tests\modules\ai_engine\features\analise_previa_mensagem\datasource\langchain_pydantic\test_pydantic_model_factory.py:14 |
| [`TestQueryCompose`](src\smart_core_assistant_painel\app\ui\treinamento\tests\test_treinamento_models.py#L97) | class | src\smart_core_assistant_painel\app\ui\treinamento\tests\test_treinamento_models.py:97 |
| [`TestServiceHub`](tests\modules\services\features\test_service_hub.py#L8) | class | tests\modules\services\features\test_service_hub.py:8 |
| [`TestSetEnvironRemoteFirebaseDatasource`](tests\modules\services\features\set_environ_remote\datasource\test_set_environ_remote_firebase_datasource.py#L35) | class | tests\modules\services\features\set_environ_remote\datasource\test_set_environ_remote_firebase_datasource.py:35 |
| [`TestSetEnvironRemoteUseCase`](tests\modules\services\features\set_environ_remote\domain\usecase\test_set_environ_remote_usecase.py#L18) | class | tests\modules\services\features\set_environ_remote\domain\usecase\test_set_environ_remote_usecase.py:18 |
| [`TestStartServices`](tests\modules\services\test_start_services.py#L18) | class | tests\modules\services\test_start_services.py:18 |
| [`TestTreinamentoAppUrls`](src\smart_core_assistant_painel\app\ui\treinamento\tests\test_treinamento_urls.py#L9) | class | src\smart_core_assistant_painel\app\ui\treinamento\tests\test_treinamento_urls.py:9 |
| [`TestTreinamentoTreinamentos`](src\smart_core_assistant_painel\app\ui\treinamento\tests\test_treinamento_models.py#L20) | class | src\smart_core_assistant_painel\app\ui\treinamento\tests\test_treinamento_models.py:20 |
| [`TestTreinamentoTreinamentosAdmin`](src\smart_core_assistant_painel\app\ui\treinamento\tests\test_treinamento_admin.py#L12) | class | src\smart_core_assistant_painel\app\ui\treinamento\tests\test_treinamento_admin.py:12 |
| [`TestTreinamentoTreinamentosAdvanced`](src\smart_core_assistant_painel\app\ui\treinamento\tests\test_treinamento_models.py#L70) | class | src\smart_core_assistant_painel\app\ui\treinamento\tests\test_treinamento_models.py:70 |
| [`TestTreinamentoTreinamentosForm`](src\smart_core_assistant_painel\app\ui\treinamento\tests\test_treinamento_forms.py#L32) | class | src\smart_core_assistant_painel\app\ui\treinamento\tests\test_treinamento_forms.py:32 |
| [`TestTreinamentoValidators`](src\smart_core_assistant_painel\app\ui\treinamento\tests\test_treinamento_models.py#L48) | class | src\smart_core_assistant_painel\app\ui\treinamento\tests\test_treinamento_models.py:48 |
| [`TestTreinamentoViews`](src\smart_core_assistant_painel\app\ui\treinamento\tests\test_treinamento_views.py#L16) | class | src\smart_core_assistant_painel\app\ui\treinamento\tests\test_treinamento_views.py:16 |
| [`TestTrelloUnifiedDataService`](tests\modules\services\features\unifield_data_services\datasource\test_trello_adapter.py#L16) | class | tests\modules\services\features\unifield_data_services\datasource\test_trello_adapter.py:16 |
| [`TestUnifieldDataServicesDatasource`](tests\modules\services\features\unifield_data_services\datasource\test_unifield_data_services_datasource.py#L23) | class | tests\modules\services\features\unifield_data_services\datasource\test_unifield_data_services_datasource.py:23 |
| [`TestUnifieldDataServicesUseCase`](tests\modules\services\features\unifield_data_services\domain\usecase\test_unifield_data_services_usecase.py#L21) | class | tests\modules\services\features\unifield_data_services\domain\usecase\test_unifield_data_services_usecase.py:21 |
| [`TestUsuariosAppUrls`](src\smart_core_assistant_painel\app\ui\usuarios\tests\test_usuarios_urls.py#L9) | class | src\smart_core_assistant_painel\app\ui\usuarios\tests\test_usuarios_urls.py:9 |
| [`TestUsuariosAppViews`](src\smart_core_assistant_painel\app\ui\usuarios\tests\test_usuarios_views.py#L9) | class | src\smart_core_assistant_painel\app\ui\usuarios\tests\test_usuarios_views.py:9 |
| [`TestVerificarTreinamentosViews`](src\smart_core_assistant_painel\app\ui\treinamento\tests\test_treinamento_views.py#L497) | class | src\smart_core_assistant_painel\app\ui\treinamento\tests\test_treinamento_views.py:497 |
| [`TestWebhookCreateList`](src\smart_core_assistant_painel\app\trello_sync\tests\test_webhook_create_list.py#L16) | class | src\smart_core_assistant_painel\app\trello_sync\tests\test_webhook_create_list.py:16 |
| [`TicketSyncService`](src\smart_core_assistant_painel\app\trello_sync\services\ticket_sync_service.py#L34) | class | src\smart_core_assistant_painel\app\trello_sync\services\ticket_sync_service.py:34 |
| [`TipoEtapa`](src\smart_core_assistant_painel\app\ui\operacional\models.py#L486) | class | src\smart_core_assistant_painel\app\ui\operacional\models.py:486 |
| [`TipoMensagem`](src\smart_core_assistant_painel\app\ui\atendimentos\models.py#L39) | class | src\smart_core_assistant_painel\app\ui\atendimentos\models.py:39 |
| [`TipoRemetente`](src\smart_core_assistant_painel\app\ui\atendimentos\models.py#L82) | class | src\smart_core_assistant_painel\app\ui\atendimentos\models.py:82 |
| [`tornar_gerente`](src\smart_core_assistant_painel\app\ui\usuarios\views.py#L153) | function | src\smart_core_assistant_painel\app\ui\usuarios\views.py:153 |
| [`touch_init`](scripts\automacao\new_feature_script.py#L50) | function | scripts\automacao\new_feature_script.py:50 |
| [`Treinamento`](src\smart_core_assistant_painel\app\ui\treinamento\models.py#L35) | class | src\smart_core_assistant_painel\app\ui\treinamento\models.py:35 |
| [`TreinamentoAdmin`](src\smart_core_assistant_painel\app\ui\treinamento\admin.py#L18) | class | src\smart_core_assistant_painel\app\ui\treinamento\admin.py:18 |
| [`TreinamentoConfig`](src\smart_core_assistant_painel\app\ui\treinamento\apps.py#L5) | class | src\smart_core_assistant_painel\app\ui\treinamento\apps.py:5 |
| [`TreinamentoService`](src\smart_core_assistant_painel\app\ui\treinamento\services.py#L13) | class | src\smart_core_assistant_painel\app\ui\treinamento\services.py:13 |
| [`TreinamentoTreinamentosForm`](src\smart_core_assistant_painel\app\ui\treinamento\tests\test_treinamento_forms.py#L10) | class | src\smart_core_assistant_painel\app\ui\treinamento\tests\test_treinamento_forms.py:10 |
| [`treinar_ia`](src\smart_core_assistant_painel\app\ui\treinamento\views.py#L69) | function | src\smart_core_assistant_painel\app\ui\treinamento\views.py:69 |
| [`TrelloBoard`](src\smart_core_assistant_painel\app\trello_sync\models.py#L7) | class | src\smart_core_assistant_painel\app\trello_sync\models.py:7 |
| [`TrelloBoardAdmin`](src\smart_core_assistant_painel\app\trello_sync\admin.py#L21) | class | src\smart_core_assistant_painel\app\trello_sync\admin.py:21 |
| [`TrelloCard`](src\smart_core_assistant_painel\app\trello_sync\models.py#L125) | class | src\smart_core_assistant_painel\app\trello_sync\models.py:125 |
| [`TrelloCardAdmin`](src\smart_core_assistant_painel\app\trello_sync\admin.py#L68) | class | src\smart_core_assistant_painel\app\trello_sync\admin.py:68 |
| [`TrelloConfigView`](src\smart_core_assistant_painel\app\tenants\views\legacy_views.py#L211) | class | src\smart_core_assistant_painel\app\tenants\views\legacy_views.py:211 |
| [`TrelloList`](src\smart_core_assistant_painel\app\trello_sync\models.py#L47) | class | src\smart_core_assistant_painel\app\trello_sync\models.py:47 |
| [`TrelloListAdmin`](src\smart_core_assistant_painel\app\trello_sync\admin.py#L42) | class | src\smart_core_assistant_painel\app\trello_sync\admin.py:42 |
| [`TrelloMember`](src\smart_core_assistant_painel\app\trello_sync\models.py#L84) | class | src\smart_core_assistant_painel\app\trello_sync\models.py:84 |
| [`TrelloMemberAdmin`](src\smart_core_assistant_painel\app\trello_sync\admin.py#L96) | class | src\smart_core_assistant_painel\app\trello_sync\admin.py:96 |
| [`TrelloSyncConfig`](src\smart_core_assistant_painel\app\trello_sync\apps.py#L4) | class | src\smart_core_assistant_painel\app\trello_sync\apps.py:4 |
| [`TrelloUnifiedDataService`](src\smart_core_assistant_painel\modules\services\features\unifield_data_services\datasource\trello_adapter.py#L24) | class | src\smart_core_assistant_painel\modules\services\features\unifield_data_services\datasource\trello_adapter.py:24 |
| [`TrelloWebhookEvent`](src\smart_core_assistant_painel\app\trello_sync\models.py#L168) | class | src\smart_core_assistant_painel\app\trello_sync\models.py:168 |
| [`TrelloWebhookEventAdmin`](src\smart_core_assistant_painel\app\trello_sync\admin.py#L120) | class | src\smart_core_assistant_painel\app\trello_sync\admin.py:120 |
| [`UnifiedDataService`](src\smart_core_assistant_painel\modules\services\features\unifield_data_services\domain\interface\unified_data_service.py#L14) | class | src\smart_core_assistant_painel\modules\services\features\unifield_data_services\domain\interface\unified_data_service.py:14 |
| [`UnifieldDataServicesDatasource`](src\smart_core_assistant_painel\modules\services\features\unifield_data_services\datasource\unifield_data_services_datasource.py#L187) | class | src\smart_core_assistant_painel\modules\services\features\unifield_data_services\datasource\unifield_data_services_datasource.py:187 |
| [`UnifieldDataServicesError`](src\smart_core_assistant_painel\modules\services\utils\erros.py#L25) | class | src\smart_core_assistant_painel\modules\services\utils\erros.py:25 |
| [`UnifieldDataServicesParameters`](src\smart_core_assistant_painel\modules\services\utils\parameters.py#L39) | class | src\smart_core_assistant_painel\modules\services\utils\parameters.py:39 |
| [`UnifieldDataServicesUseCase`](src\smart_core_assistant_painel\modules\services\features\unifield_data_services\domain\usecase\unifield_data_services_usecase.py#L16) | class | src\smart_core_assistant_painel\modules\services\features\unifield_data_services\domain\usecase\unifield_data_services_usecase.py:16 |
| [`update_env_file`](scripts\temp\trello\ngrok_trello.py#L83) | function | scripts\temp\trello\ngrok_trello.py:83 |
| [`update_features_compose`](scripts\automacao\new_feature_script.py#L341) | function | scripts\automacao\new_feature_script.py:341 |
| [`update_utils`](scripts\automacao\new_feature_script.py#L252) | function | scripts\automacao\new_feature_script.py:252 |
| [`UsuariosConfig`](src\smart_core_assistant_painel\app\ui\usuarios\apps.py#L11) | class | src\smart_core_assistant_painel\app\ui\usuarios\apps.py:11 |
| [`validate_api_key`](src\smart_core_assistant_painel\app\ui\operacional\models.py#L33) | function | src\smart_core_assistant_painel\app\ui\operacional\models.py:33 |
| [`validate_cep`](src\smart_core_assistant_painel\app\ui\clientes\models.py#L52) | function | src\smart_core_assistant_painel\app\ui\clientes\models.py:52 |
| [`validate_cnpj`](src\smart_core_assistant_painel\app\ui\clientes\models.py#L22) | function | src\smart_core_assistant_painel\app\ui\clientes\models.py:22 |
| [`validate_cpf`](src\smart_core_assistant_painel\app\ui\clientes\models.py#L37) | function | src\smart_core_assistant_painel\app\ui\clientes\models.py:37 |
| [`validate_identificador`](src\smart_core_assistant_painel\app\ui\treinamento\models.py#L17) | function | src\smart_core_assistant_painel\app\ui\treinamento\models.py:17 |
| [`validate_telefone`](src\smart_core_assistant_painel\app\ui\operacional\models.py#L20) | function | src\smart_core_assistant_painel\app\ui\operacional\models.py:20 |
| [`validate_telefone`](src\smart_core_assistant_painel\app\ui\clientes\models.py#L9) | function | src\smart_core_assistant_painel\app\ui\clientes\models.py:9 |
| [`validate_telefone_instancia`](src\smart_core_assistant_painel\app\ui\operacional\models.py#L43) | function | src\smart_core_assistant_painel\app\ui\operacional\models.py:43 |
| [`verificar_feedback_atendimento`](src\smart_core_assistant_painel\app\ui\atendimentos\tasks.py#L45) | function | src\smart_core_assistant_painel\app\ui\atendimentos\tasks.py:45 |
| [`verificar_query_compose`](src\smart_core_assistant_painel\app\ui\treinamento\views.py#L385) | function | src\smart_core_assistant_painel\app\ui\treinamento\views.py:385 |
| [`verificar_treinamentos_vetorizados`](src\smart_core_assistant_painel\app\ui\treinamento\views.py#L315) | function | src\smart_core_assistant_painel\app\ui\treinamento\views.py:315 |
| [`verify_payment_logic`](tests\verify_payment_logic.py#L29) | function | tests\verify_payment_logic.py:29 |
| [`verify_service_hub`](teste_debug\verify_service_hub.py#L23) | function | teste_debug\verify_service_hub.py:23 |
| [`webhook`](src\smart_core_assistant_painel\app\trello_sync\views_api.py#L22) | function | src\smart_core_assistant_painel\app\trello_sync\views_api.py:22 |
| [`webhook`](src\smart_core_assistant_painel\app\evolution_sync\views.py#L22) | function | src\smart_core_assistant_painel\app\evolution_sync\views.py:22 |
| [`WebhookApiTests`](src\smart_core_assistant_painel\app\trello_sync\tests\test_api_public.py#L8) | class | src\smart_core_assistant_painel\app\trello_sync\tests\test_api_public.py:8 |
| [`WebhookProcessingService`](src\smart_core_assistant_painel\app\trello_sync\services\webhook_processing_service.py#L8) | class | src\smart_core_assistant_painel\app\trello_sync\services\webhook_processing_service.py:8 |
| [`WebhookProcessor`](src\smart_core_assistant_painel\app\evolution_sync\services\webhook.py#L27) | class | src\smart_core_assistant_painel\app\evolution_sync\services\webhook.py:27 |
| [`WhiteList`](src\smart_core_assistant_painel\app\evolution_sync\models.py#L123) | class | src\smart_core_assistant_painel\app\evolution_sync\models.py:123 |
| [`WhiteListAdmin`](src\smart_core_assistant_painel\app\evolution_sync\admin.py#L11) | class | src\smart_core_assistant_painel\app\evolution_sync\admin.py:11 |

## Internal System Boundaries

Document seams between domains, bounded contexts, or service ownership. Note data ownership, synchronization strategies, and shared contract enforcement.

## External Service Dependencies

List SaaS platforms, third-party APIs, or infrastructure services the system relies on. Describe authentication methods, rate limits, and failure considerations for each dependency.

## Key Decisions & Trade-offs

Summarize architectural decisions, experiments, or ADR outcomes that shape the current design. Reference supporting documents and explain why selected approaches won over alternatives.

## Diagrams

Link architectural diagrams or add mermaid definitions here.

## Risks & Constraints

Document performance constraints, scaling considerations, or external system assumptions.

## Top Directories Snapshot
- `AGENTS.md/` — approximately 1 files
- `ambiente_cliente/` — approximately 5 files
- `ambiente_cliente_teste/` — approximately 5 files
- `bugs.txt/` — approximately 1 files
- `CHANGELOG.md/` — approximately 1 files
- `cspell.json/` — approximately 1 files
- `diagnostico_output.txt/` — approximately 1 files
- `diagnostico_result.txt/` — approximately 1 files
- `docker/` — approximately 6 files
- `docs/` — approximately 10 files
- `docs_dev/` — approximately 76 files
- `GEMINI.md/` — approximately 1 files
- `log_cluster.txt/` — approximately 1 files
- `log_langsmith.txt/` — approximately 1 files
- `log_ngrok.txt/` — approximately 1 files
- `log_servidor.txt/` — approximately 1 files
- `mkdocs.yml/` — approximately 1 files
- `openspec/` — approximately 12 files
- `pyproject.toml/` — approximately 1 files
- `pytest.ini/` — approximately 1 files
- `README.md/` — approximately 1 files
- `scripts/` — approximately 21 files
- `smartcore-landing/` — approximately 9 files
- `src/` — approximately 726 files
- `teste_debug/` — approximately 16 files
- `tests/` — approximately 344 files
- `trace.txt/` — approximately 1 files
- `uv.lock/` — approximately 1 files
- `verify_fix.py/` — approximately 1 files
- `WARP.md/` — approximately 1 files

## Related Resources

- [Project Overview](./project-overview.md)
- Update [agents/README.md](../agents/README.md) when architecture changes.

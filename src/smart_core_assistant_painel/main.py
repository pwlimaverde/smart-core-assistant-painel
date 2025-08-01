from smart_core_assistant_painel.app.ui.manage import start_app
from smart_core_assistant_painel.modules.initial_loading.start_initial_loading import (
    start_initial_loading,
)
from smart_core_assistant_painel.modules.services.start_services import start_services

if __name__ == "__main__":
    # if os.environ.get('RUN_MAIN') == 'true':
    start_initial_loading()
    start_services()
    start_app()

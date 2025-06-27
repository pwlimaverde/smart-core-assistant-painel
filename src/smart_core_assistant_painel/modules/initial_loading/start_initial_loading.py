from smart_core_assistant_painel.modules.initial_loading.features.features_compose import (
    FeaturesCompose, )


def start_initial_loading():

    FeaturesCompose.init_firebase()

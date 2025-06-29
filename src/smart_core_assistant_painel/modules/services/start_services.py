from smart_core_assistant_painel.modules.services.features.features_compose import (
    FeaturesCompose, )


def start_services():

    FeaturesCompose.set_environ_remote()
    FeaturesCompose.vetor_storage()

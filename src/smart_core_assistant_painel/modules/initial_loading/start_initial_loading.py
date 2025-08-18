from .features.features_compose import FeaturesCompose


def start_initial_loading() -> None:
    FeaturesCompose.init_firebase()

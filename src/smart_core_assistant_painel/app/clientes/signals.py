from typing import Any

import brazilcep
from django.db.models.signals import pre_save
from django.dispatch import receiver

from .models import Cliente


@receiver(pre_save, sender=Cliente)
def preencher_endereco_cep(
    sender: Any, instance: Cliente, **kwargs: Any
) -> None:
    """
    Antes de salvar um Cliente, verifica se o CEP mudou e preenche o endereço.
    """
    # Se for um objeto novo (sem pk), não há o que comparar
    if not instance.pk:
        # Se tiver um CEP, busca o endereço
        if instance.cep:
            buscar_e_preencher_endereco(instance)
        return

    # Se for um objeto existente, compara com a versão no banco
    try:
        original = sender.objects.get(pk=instance.pk)
        if original.cep != instance.cep and instance.cep:
            buscar_e_preencher_endereco(instance)
    except sender.DoesNotExist:
        # Não deveria acontecer no pre_save de um objeto existente, mas é bom ter.
        pass


def buscar_e_preencher_endereco(instance: Cliente):
    """Função auxiliar para buscar e preencher os dados do endereço."""
    try:
        cep_limpo = instance.cep.replace("-", "").replace(".", "")
        endereco = brazilcep.get_address_from_cep(cep_limpo)

        instance.logradouro = endereco.get("street", "")
        instance.bairro = endereco.get("district", "")
        instance.cidade = endereco.get("city", "")
        instance.uf = endereco.get("uf", "")
    except Exception as e:
        print(
            f"Não foi possível buscar o endereço para o CEP {instance.cep}: {e}"
        )

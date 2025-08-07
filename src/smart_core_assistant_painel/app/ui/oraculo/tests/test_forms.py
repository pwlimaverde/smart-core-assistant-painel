"""Testes para formulários do app Oraculo."""

from django.test import TestCase
from django.core.exceptions import ValidationError
from django.forms import ModelForm

from ..models import (
    Contato,
    AtendenteHumano,
    Atendimento,
    Mensagem,
    Treinamentos,
    StatusAtendimento,
    TipoMensagem,
    TipoRemetente,
)


class ContatoForm(ModelForm):
    """Formulário para modelo Contato."""
    
    class Meta:
        model = Contato
        fields = ['telefone', 'nome', 'email']
    
    def clean_telefone(self):
        """Validação customizada para telefone."""
        telefone = self.cleaned_data.get('telefone')
        if telefone:
            # Remove caracteres não numéricos
            telefone_limpo = ''.join(filter(str.isdigit, telefone))
            
            # Valida tamanho
            if len(telefone_limpo) < 10 or len(telefone_limpo) > 13:
                raise ValidationError('Telefone deve ter entre 10 e 13 dígitos.')
            
            return telefone_limpo
        return telefone


class AtendenteHumanoForm(ModelForm):
    """Formulário para modelo AtendenteHumano."""
    
    class Meta:
        model = AtendenteHumano
        fields = ['nome', 'email', 'ativo', 'especialidades']
    
    def clean_email(self):
        """Validação customizada para email."""
        email = self.cleaned_data.get('email')
        if email and AtendenteHumano.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise ValidationError('Já existe um atendente com este email.')
        return email


class AtendimentoForm(ModelForm):
    """Formulário para modelo Atendimento."""
    
    class Meta:
        model = Atendimento
        fields = ['contato', 'atendente_humano', 'status', 'observacoes']
    
    def clean(self):
        """Validação geral do formulário."""
        cleaned_data = super().clean()
        status = cleaned_data.get('status')
        atendente_humano = cleaned_data.get('atendente_humano')
        
        # Se status é HUMANO, deve ter atendente humano
        if status == StatusAtendimento.HUMANO and not atendente_humano:
            raise ValidationError('Atendimento humano requer um atendente designado.')
        
        # Se tem atendente humano, deve estar ativo
        if atendente_humano and not atendente_humano.ativo:
            raise ValidationError('Atendente selecionado não está ativo.')
        
        return cleaned_data


class MensagemForm(ModelForm):
    """Formulário para modelo Mensagem."""
    
    class Meta:
        model = Mensagem
        fields = ['atendimento', 'conteudo', 'tipo', 'remetente']
    
    def clean_conteudo(self):
        """Validação customizada para conteúdo."""
        conteudo = self.cleaned_data.get('conteudo')
        if conteudo and len(conteudo.strip()) == 0:
            raise ValidationError('Mensagem não pode estar vazia.')
        return conteudo


class TreinamentosForm(ModelForm):
    """Formulário para modelo Treinamentos."""
    
    class Meta:
        model = Treinamentos
        fields = ['pergunta', 'resposta', 'categoria', 'ativo']
    
    def clean_pergunta(self):
        """Validação customizada para pergunta."""
        pergunta = self.cleaned_data.get('pergunta')
        if pergunta and len(pergunta.strip()) < 5:
            raise ValidationError('Pergunta deve ter pelo menos 5 caracteres.')
        return pergunta
    
    def clean_resposta(self):
        """Validação customizada para resposta."""
        resposta = self.cleaned_data.get('resposta')
        if resposta and len(resposta.strip()) < 10:
            raise ValidationError('Resposta deve ter pelo menos 10 caracteres.')
        return resposta


class TestContatoForm(TestCase):
    """Testes para ContatoForm."""
    
    def test_form_valido(self) -> None:
        """Testa formulário válido."""
        form_data = {
            'telefone': '11999999999',
            'nome': 'Cliente Teste',
            'email': 'cliente@teste.com'
        }
        form = ContatoForm(data=form_data)
        
        self.assertTrue(form.is_valid())
        contato = form.save()
        self.assertEqual(contato.telefone, '11999999999')
        self.assertEqual(contato.nome, 'Cliente Teste')
    
    def test_telefone_com_formatacao(self) -> None:
        """Testa limpeza de telefone com formatação."""
        form_data = {
            'telefone': '(11) 99999-9999',
            'nome': 'Cliente Teste'
        }
        form = ContatoForm(data=form_data)
        
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['telefone'], '11999999999')
    
    def test_telefone_muito_curto(self) -> None:
        """Testa validação de telefone muito curto."""
        form_data = {
            'telefone': '119999',
            'nome': 'Cliente Teste'
        }
        form = ContatoForm(data=form_data)
        
        self.assertFalse(form.is_valid())
        self.assertIn('telefone', form.errors)
    
    def test_telefone_muito_longo(self) -> None:
        """Testa validação de telefone muito longo."""
        form_data = {
            'telefone': '551199999999999',
            'nome': 'Cliente Teste'
        }
        form = ContatoForm(data=form_data)
        
        self.assertFalse(form.is_valid())
        self.assertIn('telefone', form.errors)
    
    def test_campos_obrigatorios(self) -> None:
        """Testa validação de campos obrigatórios."""
        form = ContatoForm(data={})
        
        self.assertFalse(form.is_valid())
        # Telefone e nome são obrigatórios
        self.assertIn('telefone', form.errors)
        self.assertIn('nome', form.errors)
    
    def test_email_opcional(self) -> None:
        """Testa que email é opcional."""
        form_data = {
            'telefone': '11999999999',
            'nome': 'Cliente Teste'
            # email omitido
        }
        form = ContatoForm(data=form_data)
        
        self.assertTrue(form.is_valid())


class TestAtendenteHumanoForm(TestCase):
    """Testes para AtendenteHumanoForm."""
    
    def setUp(self) -> None:
        """Configuração inicial."""
        self.atendente_existente = AtendenteHumano.objects.create(
            nome='Atendente Existente',
            email='existente@teste.com',
            ativo=True
        )
    
    def test_form_valido(self) -> None:
        """Testa formulário válido."""
        form_data = {
            'nome': 'Novo Atendente',
            'email': 'novo@teste.com',
            'ativo': True,
            'especialidades': 'Vendas, Suporte'
        }
        form = AtendenteHumanoForm(data=form_data)
        
        self.assertTrue(form.is_valid())
        atendente = form.save()
        self.assertEqual(atendente.nome, 'Novo Atendente')
    
    def test_email_duplicado(self) -> None:
        """Testa validação de email duplicado."""
        form_data = {
            'nome': 'Outro Atendente',
            'email': 'existente@teste.com',  # Email já existe
            'ativo': True
        }
        form = AtendenteHumanoForm(data=form_data)
        
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
    
    def test_edicao_mesmo_email(self) -> None:
        """Testa que pode manter o mesmo email ao editar."""
        form_data = {
            'nome': 'Atendente Editado',
            'email': 'existente@teste.com',  # Mesmo email do atendente
            'ativo': True
        }
        form = AtendenteHumanoForm(data=form_data, instance=self.atendente_existente)
        
        self.assertTrue(form.is_valid())
    
    def test_campos_obrigatorios(self) -> None:
        """Testa validação de campos obrigatórios."""
        form = AtendenteHumanoForm(data={})
        
        self.assertFalse(form.is_valid())
        self.assertIn('nome', form.errors)
        self.assertIn('email', form.errors)


class TestAtendimentoForm(TestCase):
    """Testes para AtendimentoForm."""
    
    def setUp(self) -> None:
        """Configuração inicial."""
        self.contato = Contato.objects.create(
            telefone='11999999999',
            nome='Cliente Teste'
        )
        
        self.atendente_ativo = AtendenteHumano.objects.create(
            nome='Atendente Ativo',
            email='ativo@teste.com',
            ativo=True
        )
        
        self.atendente_inativo = AtendenteHumano.objects.create(
            nome='Atendente Inativo',
            email='inativo@teste.com',
            ativo=False
        )
    
    def test_form_valido_bot(self) -> None:
        """Testa formulário válido para atendimento por bot."""
        form_data = {
            'contato': self.contato.id,
            'status': StatusAtendimento.ATIVO,
            'observacoes': 'Atendimento por bot'
        }
        form = AtendimentoForm(data=form_data)
        
        self.assertTrue(form.is_valid())
    
    def test_form_valido_humano(self) -> None:
        """Testa formulário válido para atendimento humano."""
        form_data = {
            'contato': self.contato.id,
            'atendente_humano': self.atendente_ativo.id,
            'status': StatusAtendimento.HUMANO,
            'observacoes': 'Atendimento humano'
        }
        form = AtendimentoForm(data=form_data)
        
        self.assertTrue(form.is_valid())
    
    def test_humano_sem_atendente(self) -> None:
        """Testa validação de atendimento humano sem atendente."""
        form_data = {
            'contato': self.contato.id,
            'status': StatusAtendimento.HUMANO,
            # atendente_humano omitido
        }
        form = AtendimentoForm(data=form_data)
        
        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors)
    
    def test_atendente_inativo(self) -> None:
        """Testa validação de atendente inativo."""
        form_data = {
            'contato': self.contato.id,
            'atendente_humano': self.atendente_inativo.id,
            'status': StatusAtendimento.HUMANO
        }
        form = AtendimentoForm(data=form_data)
        
        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors)
    
    def test_campos_obrigatorios(self) -> None:
        """Testa validação de campos obrigatórios."""
        form = AtendimentoForm(data={})
        
        self.assertFalse(form.is_valid())
        self.assertIn('contato', form.errors)
        self.assertIn('status', form.errors)


class TestMensagemForm(TestCase):
    """Testes para MensagemForm."""
    
    def setUp(self) -> None:
        """Configuração inicial."""
        contato = Contato.objects.create(
            telefone='11999999999',
            nome='Cliente Teste'
        )
        
        self.atendimento = Atendimento.objects.create(
            contato=contato,
            status=StatusAtendimento.ATIVO
        )
    
    def test_form_valido(self) -> None:
        """Testa formulário válido."""
        form_data = {
            'atendimento': self.atendimento.id,
            'conteudo': 'Mensagem de teste',
            'tipo': TipoMensagem.TEXTO,
            'remetente': TipoRemetente.CONTATO
        }
        form = MensagemForm(data=form_data)
        
        self.assertTrue(form.is_valid())
        mensagem = form.save()
        self.assertEqual(mensagem.conteudo, 'Mensagem de teste')
    
    def test_conteudo_vazio(self) -> None:
        """Testa validação de conteúdo vazio."""
        form_data = {
            'atendimento': self.atendimento.id,
            'conteudo': '   ',  # Apenas espaços
            'tipo': TipoMensagem.TEXTO,
            'remetente': TipoRemetente.CONTATO
        }
        form = MensagemForm(data=form_data)
        
        self.assertFalse(form.is_valid())
        self.assertIn('conteudo', form.errors)
    
    def test_campos_obrigatorios(self) -> None:
        """Testa validação de campos obrigatórios."""
        form = MensagemForm(data={})
        
        self.assertFalse(form.is_valid())
        self.assertIn('atendimento', form.errors)
        self.assertIn('conteudo', form.errors)
        self.assertIn('tipo', form.errors)
        self.assertIn('remetente', form.errors)


class TestTreinamentosForm(TestCase):
    """Testes para TreinamentosForm."""
    
    def test_form_valido(self) -> None:
        """Testa formulário válido."""
        form_data = {
            'pergunta': 'Como posso ajudar você?',
            'resposta': 'Estou aqui para ajudar com suas dúvidas sobre nossos produtos e serviços.',
            'categoria': 'Atendimento',
            'ativo': True
        }
        form = TreinamentosForm(data=form_data)
        
        self.assertTrue(form.is_valid())
        treinamento = form.save()
        self.assertEqual(treinamento.pergunta, 'Como posso ajudar você?')
    
    def test_pergunta_muito_curta(self) -> None:
        """Testa validação de pergunta muito curta."""
        form_data = {
            'pergunta': 'Oi',  # Menos de 5 caracteres
            'resposta': 'Resposta válida com mais de 10 caracteres',
            'categoria': 'Teste'
        }
        form = TreinamentosForm(data=form_data)
        
        self.assertFalse(form.is_valid())
        self.assertIn('pergunta', form.errors)
    
    def test_resposta_muito_curta(self) -> None:
        """Testa validação de resposta muito curta."""
        form_data = {
            'pergunta': 'Pergunta válida com mais de 5 caracteres',
            'resposta': 'Curta',  # Menos de 10 caracteres
            'categoria': 'Teste'
        }
        form = TreinamentosForm(data=form_data)
        
        self.assertFalse(form.is_valid())
        self.assertIn('resposta', form.errors)
    
    def test_campos_obrigatorios(self) -> None:
        """Testa validação de campos obrigatórios."""
        form = TreinamentosForm(data={})
        
        self.assertFalse(form.is_valid())
        self.assertIn('pergunta', form.errors)
        self.assertIn('resposta', form.errors)
    
    def test_categoria_opcional(self) -> None:
        """Testa que categoria é opcional."""
        form_data = {
            'pergunta': 'Pergunta válida',
            'resposta': 'Resposta válida com mais de 10 caracteres',
            'ativo': True
            # categoria omitida
        }
        form = TreinamentosForm(data=form_data)
        
        self.assertTrue(form.is_valid())


class TestFormsIntegration(TestCase):
    """Testes de integração para formulários."""
    
    def test_fluxo_completo_atendimento(self) -> None:
        """Testa fluxo completo de criação via formulários."""
        # 1. Cria contato
        contato_form = ContatoForm(data={
            'telefone': '(11) 99999-9999',
            'nome': 'Cliente Integração',
            'email': 'integracao@teste.com'
        })
        self.assertTrue(contato_form.is_valid())
        contato = contato_form.save()
        
        # 2. Cria atendente
        atendente_form = AtendenteHumanoForm(data={
            'nome': 'Atendente Integração',
            'email': 'atendente.integracao@teste.com',
            'ativo': True,
            'especialidades': 'Suporte Técnico'
        })
        self.assertTrue(atendente_form.is_valid())
        atendente = atendente_form.save()
        
        # 3. Cria atendimento
        atendimento_form = AtendimentoForm(data={
            'contato': contato.id,
            'atendente_humano': atendente.id,
            'status': StatusAtendimento.HUMANO,
            'observacoes': 'Atendimento de integração'
        })
        self.assertTrue(atendimento_form.is_valid())
        atendimento = atendimento_form.save()
        
        # 4. Cria mensagem
        mensagem_form = MensagemForm(data={
            'atendimento': atendimento.id,
            'conteudo': 'Primeira mensagem do atendimento',
            'tipo': TipoMensagem.TEXTO,
            'remetente': TipoRemetente.CONTATO
        })
        self.assertTrue(mensagem_form.is_valid())
        mensagem = mensagem_form.save()
        
        # 5. Verifica relacionamentos
        self.assertEqual(mensagem.atendimento, atendimento)
        self.assertEqual(atendimento.contato, contato)
        self.assertEqual(atendimento.atendente_humano, atendente)
    
    def test_validacao_cruzada_formularios(self) -> None:
        """Testa validações que dependem de múltiplos formulários."""
        # Cria contato
        contato = Contato.objects.create(
            telefone='11888888888',
            nome='Cliente Validação'
        )
        
        # Tenta criar atendimento humano sem atendente ativo
        atendente_inativo = AtendenteHumano.objects.create(
            nome='Atendente Inativo',
            email='inativo@teste.com',
            ativo=False
        )
        
        atendimento_form = AtendimentoForm(data={
            'contato': contato.id,
            'atendente_humano': atendente_inativo.id,
            'status': StatusAtendimento.HUMANO
        })
        
        # Deve falhar na validação
        self.assertFalse(atendimento_form.is_valid())
        self.assertIn('__all__', atendimento_form.errors)


class TestFormsPerformance(TestCase):
    """Testes de performance para formulários."""
    
    def test_validacao_multiplos_formularios(self) -> None:
        """Testa performance de validação de múltiplos formulários."""
        import time
        
        # Prepara dados
        contatos_data = []
        for i in range(100):
            contatos_data.append({
                'telefone': f'1199999{i:04d}',
                'nome': f'Cliente {i}',
                'email': f'cliente{i}@teste.com'
            })
        
        start_time = time.time()
        
        # Valida múltiplos formulários
        forms_validos = 0
        for data in contatos_data:
            form = ContatoForm(data=data)
            if form.is_valid():
                forms_validos += 1
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Validação de 100 formulários deve ser rápida
        self.assertLess(execution_time, 2.0)
        self.assertEqual(forms_validos, 100)
    
    def test_salvamento_multiplos_formularios(self) -> None:
        """Testa performance de salvamento de múltiplos formulários."""
        import time
        
        start_time = time.time()
        
        # Salva múltiplos formulários
        for i in range(50):
            form = ContatoForm(data={
                'telefone': f'1188888{i:04d}',
                'nome': f'Cliente Performance {i}'
            })
            if form.is_valid():
                form.save()
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Salvamento de 50 formulários deve ser razoavelmente rápido
        self.assertLess(execution_time, 5.0)
        
        # Verifica que todos foram salvos
        count = Contato.objects.filter(nome__startswith='Cliente Performance').count()
        self.assertEqual(count, 50)
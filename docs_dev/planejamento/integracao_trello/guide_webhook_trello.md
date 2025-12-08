# Guia: Configurar Webhook para Área de Trabalho (Workspace) no Trello

Este guia descreve como registrar uma URI para receber eventos de uma Área de Trabalho via API do Trello.

## 1. Obter Credenciais de API
Para interagir com a API, você precisa de uma chave e um token.
1. Acesse **[trello.com/app-key](https://trello.com/app-key)**.
2. Copie a **Key** (Chave de API).
3. Na mesma página, clique no link para gerar um **Token** manualmente e autorize o acesso.
4. Guarde a **Key** e o **Token**.

## 2. Obter o ID da Área de Trabalho (`idModel`)
O webhook precisa do ID técnico da organização (Workspace), não do nome.
1. Abra qualquer **Quadro (Board)** que esteja dentro da Área de Trabalho que deseja monitorar.
2. Adicione `.json` ao final da URL do quadro no navegador.
   * *Exemplo:* `https://trello.com/b/xyz123/nome-do-quadro.json`
3. No JSON exibido, pesquise (Ctrl+F) por `"idOrganization"`.
4. Copie o valor ao lado (ex: `"5abcd...123"`). Este será usado como **idModel**.

## 3. Pré-requisito do Servidor (URI)
**Atenção:** Antes de criar o webhook, sua rota (`callbackURL`) já deve estar online.
* No momento da criação, o Trello faz uma requisição do tipo **`HEAD`** para verificar a URL.
* Se a sua rota não retornar status `200 OK` para essa requisição `HEAD`, o webhook não será criado.

## 4. Comando para Criar o Webhook
Use o comando `cURL` abaixo no seu terminal para registrar o webhook. Substitua os valores em maiúsculo pelos seus dados.

```bash
curl -X POST "https://api.trello.com/1/webhooks/" \
  -d key="SUA_API_KEY" \
  -d token="SEU_API_TOKEN" \
  -d callbackURL="HTTPS://SUA-URL.COM/SEU-ENDPOINT" \
  -d idModel="ID_DA_ORGANIZACAO" \
  -d description="Webhook do Workspace Trello"


5. Validação
Sucesso: A API retornará um JSON com os dados do webhook e "active": true.
Erro: Se receber erro, verifique se sua callbackURL está acessível publicamente e respondendo a requisições HEAD.
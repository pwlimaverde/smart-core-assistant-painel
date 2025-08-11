# Facilita importações absolutas do pacote `oraculo` para ferramentas de type checking
# e para import paths em Django (apps.py define label="oraculo").
# 
# IMPORTANTE: Não importar models, views ou utils no nível superior para evitar
# AppRegistryNotReady durante a inicialização do Django. O Django precisa
# carregar todos os apps antes que os models sejam importados.
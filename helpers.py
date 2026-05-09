# =============================================================================
# helpers.py — Funções Auxiliares (Validações, API e Exportação)
# =============================================================================
#
# O QUE É UM MÓDULO AUXILIAR?
# ----------------------------
# Em projetos reais, separamos o código em arquivos com responsabilidades
# bem definidas. Esse arquivo concentra funções que:
#   1. Validam os dados antes de salvar no banco
#   2. Consultam a API externa ViaCEP
#   3. Exportam os dados para CSV
#
# Isso torna o app.py mais limpo e as funções mais fáceis de testar
# (veremos isso na Hora 4 — Testes Unitários).
#
# =============================================================================

import os         # Manipulação de caminhos de arquivos
import requests   # Biblioteca instalada via pip: faz requisições HTTP

# Caminho para a pasta de dados
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# =============================================================================
# BLOCO 1: VALIDAÇÕES
# =============================================================================

def validar_nome(nome):
    """
    Valida o campo nome do aluno.

    Regras:
    - Não pode ser vazio ou só espaços
    - Deve ter pelo menos 3 caracteres
    - Deve ter no máximo 100 caracteres

    Retorna:
        (True, '')           → válido
        (False, 'mensagem')  → inválido, com motivo
    """
    nome = nome.strip()  # Remove espaços do início e fim

    if not nome:
        return False, 'O nome não pode ser vazio.'

    if len(nome) < 3:
        return False, 'O nome deve ter pelo menos 3 caracteres.'

    if len(nome) > 100:
        return False, 'O nome deve ter no máximo 100 caracteres.'

    return True, ''


def validar_nota(nota_str):
    """
    Valida o campo nota do aluno.

    Regras:
    - Deve ser um número (inteiro ou decimal)
    - Deve estar entre 0.0 e 10.0 (inclusive)

    Por que recebemos uma string?
    ------------------------------
    Formulários HTML sempre enviam os dados como texto (string).
    Precisamos tentar converter para float antes de validar.

    Retorna:
        (True, float)        → válido, com o valor convertido
        (False, 'mensagem')  → inválido, com motivo
    """
    try:
        nota = float(nota_str)  # Tenta converter string → número decimal
    except (ValueError, TypeError):
        # ValueError: quando a string não é um número (ex: 'abc')
        # TypeError:  quando o valor é None (campo não preenchido)
        return False, 'A nota deve ser um número válido.'

    if nota < 0.0 or nota > 10.0:
        return False, 'A nota deve estar entre 0 e 10.'

    return True, nota


def validar_cep(cep):
    """
    Valida o formato do CEP.

    Um CEP brasileiro tem 8 dígitos numéricos.
    Aqui removemos traços e espaços antes de validar.

    Retorna:
        (True, '17501010')   → válido, CEP apenas com dígitos
        (False, 'mensagem')  → inválido
    """
    cep_limpo = cep.replace('-', '').replace(' ', '').strip()

    if not cep_limpo:
        return True, ''  # CEP é opcional — se vazio, retorna True sem valor

    if not cep_limpo.isdigit():
        return False, 'O CEP deve conter apenas números.'

    if len(cep_limpo) != 8:
        return False, 'O CEP deve ter 8 dígitos.'

    return True, cep_limpo


# =============================================================================
# BLOCO 2: CONSUMO DA API VIACEP
# =============================================================================

def buscar_endereco_por_cep(cep):
    """
    Consulta a API pública ViaCEP para obter o endereço completo de um CEP.

    O QUE É UMA API?
    ----------------
    API (Application Programming Interface) é um serviço externo que
    disponibiliza dados pela internet. Fazemos uma requisição HTTP (GET)
    para a URL da API e recebemos os dados em formato JSON.

    JSON (JavaScript Object Notation):
    -----------------------------------
    Formato leve de troca de dados, parecido com um dicionário Python:
    {
        "cep": "17501-010",
        "logradouro": "Rua Boa Morte",
        "bairro": "Centro",
        "localidade": "Marília",
        "uf": "SP"
    }

    A BIBLIOTECA requests:
    ----------------------
    requests.get(url)  → faz uma requisição HTTP do tipo GET para a URL
    response.json()    → converte a resposta JSON em dicionário Python
    response.status_code → código HTTP (200 = sucesso, 404 = não encontrado)

    Tratamento de erros:
    --------------------
    Usamos try/except para capturar falhas de rede (sem internet,
    timeout, servidor fora do ar). Isso evita que o sistema quebre.

    Parâmetros:
        cep (str): CEP com 8 dígitos, sem traço

    Retorna:
        dict com endereço → sucesso
        None              → CEP inválido ou erro de rede
    """
    if not cep or len(cep) != 8:
        return None

    url = f'https://viacep.com.br/ws/{cep}/json/'

    try:
        # timeout=5 → espera no máximo 5 segundos pela resposta
        response = requests.get(url, timeout=5)

        # Verifica se a requisição foi bem-sucedida (status 200)
        if response.status_code == 200:
            dados = response.json()

            # A API retorna {"erro": true} quando o CEP não existe
            if 'erro' in dados:
                return None

            # Retornamos apenas os campos que precisamos
            return {
                'logradouro': dados.get('logradouro', ''),
                'bairro':     dados.get('bairro', ''),
                'cidade':     dados.get('localidade', ''),
                'uf':         dados.get('uf', '')
            }

    except requests.exceptions.ConnectionError:
        # Sem conexão com a internet
        print('[AVISO] Sem conexão com a internet. ViaCEP indisponível.')
    except requests.exceptions.Timeout:
        # A requisição demorou mais de 5 segundos
        print('[AVISO] Timeout ao consultar ViaCEP.')
    except requests.exceptions.RequestException as e:
        # Qualquer outro erro da biblioteca requests
        print(f'[ERRO] Falha ao consultar ViaCEP: {e}')

    return None  # Em caso de qualquer erro, retorna None

# =============================================================================
# BLOCO 3: REGRA DE NEGÓCIOS
# =============================================================================
def calcular_situacao(nota):
    """
    Retorna a situação do aluno com base na nota.

    Regras:
    - Nota >= 7.0 → Aprovado
    - Nota >= 5.0 → Recuperação
    - Nota < 5.0  → Reprovado

    Parâmetros:
        nota (float): nota do aluno

    Retorna:
        str: 'Aprovado', 'Recuperação' ou 'Reprovado'
    """
    if nota >= 7.0:
        return 'Aprovado'
    elif nota >= 5.0:
        return 'Recuperação'
    else:
        return 'Reprovado'
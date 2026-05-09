# =============================================================================
# database.py — Módulo de Persistência com SQLite3
# =============================================================================
#
# O QUE É O SQLITE3?
# ------------------
# SQLite3 é um banco de dados relacional embutido no próprio Python.
# Não precisa de instalação separada, nem de um servidor rodando.
# Os dados ficam salvos em um único arquivo (.db) na pasta do projeto.
#
# CONCEITOS IMPORTANTES:
# ----------------------
#  - Banco de dados: local onde os dados ficam armazenados de forma organizada
#  - Tabela: estrutura com linhas (registros) e colunas (campos), como uma planilha
#  - SQL: linguagem usada para criar, ler, atualizar e deletar dados
#  - CRUD: Create, Read, Update, Delete — as 4 operações básicas de qualquer sistema
#
# COMANDOS SQL QUE USAREMOS:
# --------------------------
#  CREATE TABLE  → cria uma tabela nova
#  INSERT INTO   → insere um novo registro
#  SELECT        → busca/lê registros
#  UPDATE        → atualiza um registro existente
#  DELETE        → remove um registro
#
# =============================================================================

import sqlite3  # Biblioteca nativa do Python — não precisa instalar!
import os       # Para manipular caminhos de arquivos

# Caminho onde o arquivo do banco de dados será salvo
# os.path.dirname(__file__)  → pasta onde este arquivo (database.py) está
# os.path.join(...)          → monta o caminho completo de forma segura
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'data', 'alunos.db')


def get_connection():
    """
    Cria e retorna uma conexão com o banco de dados SQLite3.

    O que é uma conexão?
    --------------------
    É o "canal" de comunicação entre o Python e o banco de dados.
    Sempre que queremos ler ou gravar dados, precisamos de uma conexão aberta.

    row_factory = sqlite3.Row
    -------------------------
    Por padrão, os resultados do SQLite vêm como tuplas: (1, 'João', 8.5, ...)
    Com row_factory, os resultados se comportam como dicionários:
    aluno['nome'], aluno['nota'] — muito mais legível!
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Resultados acessíveis por nome de coluna
    return conn


def criar_tabela():
    """
    Cria a tabela 'alunos' no banco de dados, se ela ainda não existir.

    Estrutura da tabela:
    --------------------
    id        → número inteiro, chave primária, incrementado automaticamente
    nome      → texto, obrigatório (NOT NULL)
    nota      → número decimal entre 0 e 10
    cep       → texto do CEP (somente números, ex: '17501010')
    logradouro→ rua/avenida obtida da API ViaCEP
    bairro    → bairro obtido da API ViaCEP
    cidade    → cidade obtida da API ViaCEP
    uf        → estado (sigla) obtido da API ViaCEP

    IF NOT EXISTS → só cria a tabela se ela não existir ainda.
                    Isso evita erros ao reiniciar a aplicação.
    """
    conn = get_connection()

    # O triple-quote (""") permite escrever strings em várias linhas — ideal para SQL
    conn.execute("""
        CREATE TABLE IF NOT EXISTS alunos (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            nome        TEXT    NOT NULL,
            nota        REAL    NOT NULL,
            cep         TEXT,
            logradouro  TEXT,
            bairro      TEXT,
            cidade      TEXT,
            uf          TEXT
        )
    """)

    conn.commit()   # Confirma ("salva") as alterações no banco
    conn.close()    # Fecha a conexão para liberar recursos


def inserir_aluno(nome, nota, cep='', logradouro='', bairro='', cidade='', uf=''):
    """
    Insere um novo aluno na tabela.

    Parâmetros nomeados com valor padrão:
    --------------------------------------
    Os campos de endereço têm valor padrão '' (string vazia), ou seja,
    são opcionais — o cadastro funciona mesmo sem CEP.

    Por que usamos '?' no lugar dos valores?
    -----------------------------------------
    Isso se chama "parametrização de queries" ou "prepared statements".
    É uma proteção contra SQL Injection — um tipo de ataque em que alguém
    tenta inserir comandos SQL maliciosos nos campos do formulário.

    NUNCA faça assim (vulnerável):
        conn.execute(f"INSERT INTO alunos VALUES ('{nome}', {nota})")

    SEMPRE faça assim (seguro):
        conn.execute("INSERT INTO alunos VALUES (?, ?)", (nome, nota))
    """
    conn = get_connection()
    conn.execute(
        """
        INSERT INTO alunos (nome, nota, cep, logradouro, bairro, cidade, uf)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (nome, nota, cep, logradouro, bairro, cidade, uf)
    )
    conn.commit()
    conn.close()


def listar_alunos():
    """
    Retorna todos os alunos cadastrados, ordenados pelo nome.

    SELECT * FROM alunos
    --------------------
    SELECT → seleciona dados
    *      → todas as colunas
    FROM   → de qual tabela

    ORDER BY nome → ordena os resultados em ordem alfabética pelo nome

    fetchall()
    ----------
    Busca TODOS os registros que o SELECT retornou.
    Cada item da lista se comporta como um dicionário (por causa do row_factory).
    """
    conn = get_connection()
    cursor = conn.execute("SELECT * FROM alunos ORDER BY nome")
    alunos = cursor.fetchall()
    conn.close()
    return alunos


def buscar_aluno_por_id(aluno_id):
    """
    Retorna um único aluno pelo seu ID.

    WHERE id = ?
    ------------
    WHERE → filtra os resultados (como um "if" no SQL)
    id = ?→ queremos apenas o aluno cujo id seja igual ao valor passado

    fetchone()
    ----------
    Busca apenas UM registro (o primeiro que corresponder ao filtro).
    Retorna None se nenhum registro for encontrado.
    """
    conn = get_connection()
    cursor = conn.execute("SELECT * FROM alunos WHERE id = ?", (aluno_id,))
    aluno = cursor.fetchone()
    conn.close()
    return aluno


def atualizar_aluno(aluno_id, nome, nota, cep='', logradouro='', bairro='', cidade='', uf=''):
    """
    Atualiza os dados de um aluno existente.

    UPDATE alunos SET ...
    ---------------------
    UPDATE → atualiza registros existentes
    SET    → define quais colunas serão alteradas e com quais valores
    WHERE  → MUITO IMPORTANTE! Sem o WHERE, TODOS os registros seriam alterados.
             Sempre filtre pelo ID para atualizar apenas o aluno desejado.
    """
    conn = get_connection()
    conn.execute(
        """
        UPDATE alunos
        SET nome = ?, nota = ?, cep = ?, logradouro = ?, bairro = ?, cidade = ?, uf = ?
        WHERE id = ?
        """,
        (nome, nota, cep, logradouro, bairro, cidade, uf, aluno_id)
    )
    conn.commit()
    conn.close()


def deletar_aluno(aluno_id):
    """
    Remove um aluno do banco de dados pelo seu ID.

    DELETE FROM alunos WHERE id = ?
    --------------------------------
    DELETE FROM → remove registros da tabela
    WHERE       → filtra qual registro será removido
    ATENÇÃO: sem WHERE, TODOS os registros seriam deletados!
    """
    conn = get_connection()
    conn.execute("DELETE FROM alunos WHERE id = ?", (aluno_id,))
    conn.commit()
    conn.close()


def contar_alunos():
    """
    Retorna o número total de alunos cadastrados.

    COUNT(*) é uma função agregada do SQL:
    ela conta quantas linhas existem na tabela.
    """
    conn = get_connection()
    cursor = conn.execute("SELECT COUNT(*) FROM alunos")
    total = cursor.fetchone()[0]  # fetchone retorna uma tupla; [0] pega o primeiro valor
    conn.close()
    return total


def media_turma():
    """
    Calcula a média das notas de todos os alunos.

    AVG() é outra função agregada do SQL:
    ela calcula a média dos valores de uma coluna.
    ROUND(..., 2) arredonda para 2 casas decimais.
    """
    conn = get_connection()
    cursor = conn.execute("SELECT ROUND(AVG(nota), 2) FROM alunos")
    media = cursor.fetchone()[0]
    conn.close()
    return media if media is not None else 0.0

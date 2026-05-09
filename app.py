# Arquivo principal da aplicação Flask

# Importa a classe Flask do pacote Flask
from flask import Flask, render_template, flash, redirect, url_for, request

#iporta os pacotes internos
import database as db
import helpers

# Cria a instância da aplicação
# __name__ diz ao Flask onde está a raiz do projeto
app = Flask(__name__)

# Chave secreta - usada para proteger sessões
# e formulários CSRF
app.config['SECRET_KEY'] = 'trocar_senha'
db.criar_tabela()  # Garante que a tabela 'alunos' exista no banco de dados

# Rota principal
# http://localhost:5000 , retorna Olá
@app.route('/')
def index():
    alunos = db.listar_alunos()  # Busca os alunos do banco de dados
    total = db.contar_alunos()   # Busca o total de alunos
    media = db.media_turma()     # Calcula a média das notas
    
    alunos_com_situacao = [
        {
            'id':         aluno['id'],
            'nome':       aluno['nome'],
            'nota':       aluno['nota'],
            'situacao':   helpers.calcular_situacao(aluno['nota']),
            'cep':        aluno['cep'],
            'logradouro': aluno['logradouro'],
            'bairro':     aluno['bairro'],
            'cidade':     aluno['cidade'],
            'uf':         aluno['uf']
        }
        for aluno in alunos
    ]
    
    return render_template('index.html', alunos=alunos_com_situacao, total=total, media=media)

@app.route('/cadastrar', methods=['GET', 'POST'])
def cadastrar():
    """
    ROTA: GET e POST /cadastrar
    ---------------------------
    GET  → Exibe o formulário de cadastro em branco
    POST → Recebe e processa os dados do formulário

    Por que a mesma rota trata GET e POST?
    ---------------------------------------
    É uma prática comum em Flask usar a mesma URL para exibir
    e processar um formulário. Verificamos o método com request.method.

    request.form
    ------------
    Dicionário com os dados enviados pelo formulário HTML.
    As chaves são os atributos name="" dos campos do formulário.
    Ex: <input name="nome"> → request.form['nome']

    flash()
    -------
    Exibe uma mensagem temporária para o usuário (feedback visual).
    Aparece apenas na próxima requisição e desaparece depois.
    Categorias: 'success' (verde), 'danger' (vermelho), 'warning' (amarelo)

    redirect() e url_for()
    ----------------------
    redirect()  → redireciona o navegador para outra URL
    url_for()   → gera a URL de uma função de rota pelo nome da função
    Exemplo: url_for('index') → '/'
    Por que usar url_for em vez de '/' direto?
    Se você mudar a rota, url_for se adapta automaticamente.
    """
    if request.method == 'POST':
        # ── 1. Capturar dados do formulário ──────────────────────────────────
        nome_bruto = request.form.get('nome', '')
        nota_bruta = request.form.get('nota', '')
        cep_bruto  = request.form.get('cep', '')

        erros = []  # Lista para acumular mensagens de erro

        # ── 2. Validar nome ──────────────────────────────────────────────────
        nome_valido, msg_nome = helpers.validar_nome(nome_bruto)
        if not nome_valido:
            erros.append(msg_nome)

        # ── 3. Validar nota ──────────────────────────────────────────────────
        nota_valida, resultado_nota = helpers.validar_nota(nota_bruta)
        if not nota_valida:
            erros.append(resultado_nota)
        else:
            nota = resultado_nota  # resultado_nota é o float convertido

        # ── 4. Validar e processar CEP ───────────────────────────────────────
        cep_valido, cep_limpo = helpers.validar_cep(cep_bruto)
        if not cep_valido:
            erros.append(cep_limpo)  # cep_limpo contém a mensagem de erro nesse caso

        # ── 5. Se há erros, volta ao formulário com as mensagens ─────────────
        if erros:
            for erro in erros:
                flash(erro, 'danger')  # 'danger' → alerta vermelho no Bootstrap
            return render_template('cadastro.html')

        # ── 6. Buscar endereço na API ViaCEP (se CEP foi informado) ──────────
        logradouro = bairro = cidade = uf = ''

        if cep_limpo:
            endereco = helpers.buscar_endereco_por_cep(cep_limpo)
            if endereco:
                logradouro = endereco['logradouro']
                bairro     = endereco['bairro']
                cidade     = endereco['cidade']
                uf         = endereco['uf']
            else:
                flash('CEP não encontrado. Endereço não preenchido automaticamente.', 'warning')

        # ── 7. Inserir no banco de dados ─────────────────────────────────────
        db.inserir_aluno(
            nome=nome_bruto.strip(),
            nota=nota,
            cep=cep_limpo,
            logradouro=logradouro,
            bairro=bairro,
            cidade=cidade,
            uf=uf
        )

        flash(f'Aluno "{nome_bruto.strip()}" cadastrado com sucesso!', 'success')
        return redirect(url_for('index'))  # Redireciona para a lista

    # ── GET: exibe o formulário vazio ─────────────────────────────────────────
    return render_template('cadastro.html')

@app.route('/editar/<int:aluno_id>', methods=['GET', 'POST'])
def editar(aluno_id):
    """
    ROTA: GET e POST /editar/<id>
    ------------------------------
    <int:aluno_id> → parâmetro dinâmico na URL
    O Flask converte automaticamente para inteiro (int:).

    Exemplo: /editar/3 → aluno_id = 3

    GET  → Exibe o formulário pré-preenchido com os dados do aluno
    POST → Processa as alterações e salva no banco

    Retorna 404 implicitamente se o aluno não existir.
    """
    aluno = db.buscar_aluno_por_id(aluno_id)

    # Se o aluno não existir no banco, exibe mensagem e redireciona
    if aluno is None:
        flash('Aluno não encontrado.', 'danger')
        return redirect(url_for('index'))

    if request.method == 'POST':
        nome_bruto = request.form.get('nome', '')
        nota_bruta = request.form.get('nota', '')
        cep_bruto  = request.form.get('cep', '')

        erros = []

        nome_valido, msg_nome = helpers.validar_nome(nome_bruto)
        if not nome_valido:
            erros.append(msg_nome)

        nota_valida, resultado_nota = helpers.validar_nota(nota_bruta)
        if not nota_valida:
            erros.append(resultado_nota)
        else:
            nota = resultado_nota

        cep_valido, cep_limpo = helpers.validar_cep(cep_bruto)
        if not cep_valido:
            erros.append(cep_limpo)

        if erros:
            for erro in erros:
                flash(erro, 'danger')
            # Passa o aluno de volta para pré-preencher o formulário
            return render_template('editar.html', aluno=aluno)

        logradouro = bairro = cidade = uf = ''

        if cep_limpo:
            endereco = helpers.buscar_endereco_por_cep(cep_limpo)
            if endereco:
                logradouro = endereco['logradouro']
                bairro     = endereco['bairro']
                cidade     = endereco['cidade']
                uf         = endereco['uf']
            else:
                flash('CEP não encontrado. Endereço não atualizado.', 'warning')
                # Mantém o endereço anterior
                logradouro = aluno['logradouro'] or ''
                bairro     = aluno['bairro'] or ''
                cidade     = aluno['cidade'] or ''
                uf         = aluno['uf'] or ''

        db.atualizar_aluno(
            aluno_id=aluno_id,
            nome=nome_bruto.strip(),
            nota=nota,
            cep=cep_limpo,
            logradouro=logradouro,
            bairro=bairro,
            cidade=cidade,
            uf=uf
        )

        flash(f'Aluno "{nome_bruto.strip()}" atualizado com sucesso!', 'success')
        return redirect(url_for('index'))

    return render_template('editar.html', aluno=aluno)


@app.route('/deletar/<int:aluno_id>', methods=['POST'])
def deletar(aluno_id):
    """
    ROTA: POST /deletar/<id>
    -------------------------
    Por que só POST e não GET?
    --------------------------
    Nunca use GET para operações destrutivas (deletar, alterar estado).
    Um link GET pode ser acessado acidentalmente (bot, pré-load do navegador).
    POST exige uma ação intencional do usuário (clicar em um botão de formulário).

    No HTML, usamos um <form method="POST"> com um <button> para chamar essa rota.
    """
    aluno = db.buscar_aluno_por_id(aluno_id)

    if aluno is None:
        flash('Aluno não encontrado.', 'danger')
    else:
        db.deletar_aluno(aluno_id)
        flash(f'Aluno "{aluno["nome"]}" removido com sucesso.', 'success')

    return redirect(url_for('index'))

# Debug
if __name__ == '__main__':
    app.run(debug=True)

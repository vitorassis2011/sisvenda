import sqlite3
from datetime import datetime

# ==================== CONEXÃO COM O BANCO ====================
def conectar():
    conn = sqlite3.connect('sisivenda.db')
    return conn

# ==================== CRIAÇÃO DAS TABELAS ====================
def criar_tabelas():
    conn = conectar()
    cursor = conn.cursor()

    # Tabela de Clientes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            cpf TEXT UNIQUE,
            telefone TEXT,
            endereco TEXT
        )
    ''')

    # Tabela de Produtos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            preco REAL NOT NULL,
            estoque INTEGER NOT NULL DEFAULT 0
        )
    ''')

    # Tabela de Vendas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vendas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT NOT NULL,
            cliente_id INTEGER,
            total REAL NOT NULL,
            FOREIGN KEY (cliente_id) REFERENCES clientes(id)
        )
    ''')

    # Tabela de Itens da Venda
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS itens_venda (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            venda_id INTEGER,
            produto_id INTEGER,
            quantidade INTEGER NOT NULL,
            preco_unitario REAL NOT NULL,
            subtotal REAL NOT NULL,
            FOREIGN KEY (venda_id) REFERENCES vendas(id),
            FOREIGN KEY (produto_id) REFERENCES produtos(id)
        )
    ''')

    conn.commit()
    conn.close()
    print("Banco de dados e tabelas criados com sucesso!\n")

# ==================== FUNÇÕES DE CLIENTES ====================
def cadastrar_cliente():
    nome = input("Nome do cliente: ")
    cpf = input("CPF (opcional): ") or None
    telefone = input("Telefone: ")
    endereco = input("Endereço: ")

    conn = conectar()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO clientes (nome, cpf, telefone, endereco) VALUES (?, ?, ?, ?)",
                       (nome, cpf, telefone, endereco))
        conn.commit()
        print("Cliente cadastrado com sucesso!\n")
    except sqlite3.IntegrityError:
        print("Erro: CPF já cadastrado!\n")
    finally:
        conn.close()

def listar_clientes():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM clientes")
    clientes = cursor.fetchall()
    conn.close()

    if not clientes:
        print("Nenhum cliente cadastrado.\n")
        return

    print(f"{'ID':<5} {'Nome':<25} {'CPF':<15} {'Telefone':<15}")
    print("-" * 70)
    for c in clientes:
        print(f"{c[0]:<5} {c[1]:<25} {c[2] or '':<15} {c[3]:<15}")

# ==================== FUNÇÕES DE PRODUTOS ====================
def cadastrar_produto():
    nome = input("Nome do produto: ")
    preco = float(input("Preço (R$): "))
    estoque = int(input("Quantidade em estoque: "))

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO produtos (nome, preco, estoque) VALUES (?, ?, ?)",
                   (nome, preco, estoque))
    conn.commit()
    conn.close()
    print("Produto cadastrado com sucesso!\n")

def listar_produtos():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM produtos")
    produtos = cursor.fetchall()
    conn.close()

    if not produtos:
        print("Nenhum produto cadastrado.\n")
        return

    print(f"{'ID':<5} {'Produto':<30} {'Preço (R$)':<12} {'Estoque':<8}")
    print("-" * 60)
    for p in produtos:
        print(f"{p[0]:<5} {p[1]:<30} {p[2]:<12.2f} {p[3]:<8}")

# ==================== FUNÇÃO DE VENDA ====================
def realizar_venda():
    listar_clientes()
    cliente_id = int(input("\nDigite o ID do cliente (0 para venda sem cliente): ") or 0)

    if cliente_id == 0:
        cliente_id = None

    itens = []
    total_venda = 0.0

    while True:
        listar_produtos()
        prod_id = int(input("\nDigite o ID do produto (0 para finalizar venda): "))
        if prod_id == 0:
            break

        quantidade = int(input("Quantidade: "))

        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT nome, preco, estoque FROM produtos WHERE id = ?", (prod_id,))
        produto = cursor.fetchone()

        if not produto:
            print("Produto não encontrado!")
            conn.close()
            continue

        nome_prod, preco, estoque = produto

        if quantidade > estoque:
            print(f"Estoque insuficiente! Disponível: {estoque}")
            conn.close()
            continue

        subtotal = preco * quantidade
        total_venda += subtotal

        itens.append((prod_id, quantidade, preco, subtotal))
        print(f"{quantidade}x {nome_prod} - Subtotal: R$ {subtotal:.2f}\n")
        conn.close()

    if not itens:
        print("Venda cancelada. Nenhum item adicionado.\n")
        return

    # Registrar a venda
    data_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("INSERT INTO vendas (data, cliente_id, total) VALUES (?, ?, ?)",
                   (data_atual, cliente_id, total_venda))
    venda_id = cursor.lastrowid

    # Registrar itens da venda e atualizar estoque
    for prod_id, qtd, preco_unit, subtotal in itens:
        cursor.execute("""
            INSERT INTO itens_venda (venda_id, produto_id, quantidade, preco_unitario, subtotal)
            VALUES (?, ?, ?, ?, ?)
        """, (venda_id, prod_id, qtd, preco_unit, subtotal))

        # Baixa no estoque
        cursor.execute("UPDATE produtos SET estoque = estoque - ? WHERE id = ?", (qtd, prod_id))

    conn.commit()
    conn.close()

    print(f"\nVenda realizada com sucesso! ID da venda: {venda_id}")
    print(f"Total da venda: R$ {total_venda:.2f}\n")

# ==================== RELATÓRIOS ====================
def listar_vendas():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT v.id, v.data, c.nome, v.total 
        FROM vendas v 
        LEFT JOIN clientes c ON v.cliente_id = c.id 
        ORDER BY v.id DESC
    """)
    vendas = cursor.fetchall()
    conn.close()

    if not vendas:
        print("Nenhuma venda registrada.\n")
        return

    print(f"{'ID':<5} {'Data':<20} {'Cliente':<25} {'Total (R$)':<12}")
    print("-" * 70)
    for v in vendas:
        cliente = v[2] if v[2] else "Sem cliente"
        print(f"{v[0]:<5} {v[1]:<20} {cliente:<25} {v[3]:<12.2f}")

# ==================== MENU PRINCIPAL ====================
def menu():
    criar_tabelas()

    while True:
        print("\n" + "="*40)
        print("          SISIVENDA - Sistema de Vendas")
        print("="*40)
        print("1. Cadastrar Cliente")
        print("2. Listar Clientes")
        print("3. Cadastrar Produto")
        print("4. Listar Produtos")
        print("5. Realizar Venda")
        print("6. Listar Vendas")
        print("0. Sair")
        print("="*40)

        opcao = input("Escolha uma opção: ")

        if opcao == "1":
            cadastrar_cliente()
        elif opcao == "2":
            listar_clientes()
        elif opcao == "3":
            cadastrar_produto()
        elif opcao == "4":
            listar_produtos()
        elif opcao == "5":
            realizar_venda()
        elif opcao == "6":
            listar_vendas()
        elif opcao == "0":
            print("Saindo do sistema... Até logo!")
            break
        else:
            print("Opção inválida! Tente novamente.")

if __name__ == "__main__":
    menu()

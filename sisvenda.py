import sqlite3
import datetime
from tabulate import tabulate

# ====================== CONEXÃO COM O BANCO ======================
def conectar():
    conn = sqlite3.connect('sisvenda.db')
    conn.row_factory = sqlite3.Row
    return conn

def criar_tabelas():
    conn = conectar()
    cursor = conn.cursor()
    
    cursor.executescript('''
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            cpf TEXT UNIQUE,
            telefone TEXT,
            email TEXT,
            endereco TEXT
        );
        
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            preco REAL NOT NULL,
            estoque INTEGER DEFAULT 0,
            categoria TEXT
        );
        
        CREATE TABLE IF NOT EXISTS vendas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT NOT NULL,
            cliente_id INTEGER,
            total REAL NOT NULL,
            FOREIGN KEY (cliente_id) REFERENCES clientes(id)
        );
        
        CREATE TABLE IF NOT EXISTS itens_venda (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            venda_id INTEGER,
            produto_id INTEGER,
            quantidade INTEGER,
            preco_unitario REAL,
            FOREIGN KEY (venda_id) REFERENCES vendas(id),
            FOREIGN KEY (produto_id) REFERENCES produtos(id)
        );
    ''')
    conn.commit()
    conn.close()

# ====================== FUNÇÕES AUXILIARES ======================
def limpar_tela():
    import os
    os.system('cls' if os.name == 'nt' else 'clear')

# ====================== CLIENTES ======================
def cadastrar_cliente():
    nome = input("Nome: ")
    cpf = input("CPF: ")
    telefone = input("Telefone: ")
    email = input("Email: ")
    endereco = input("Endereço: ")
    
    conn = conectar()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO clientes (nome, cpf, telefone, email, endereco) VALUES (?,?,?,?,?)",
                      (nome, cpf, telefone, email, endereco))
        conn.commit()
        print("✅ Cliente cadastrado com sucesso!")
    except sqlite3.IntegrityError:
        print("❌ CPF já cadastrado!")
    conn.close()

# ====================== PRODUTOS ======================
def cadastrar_produto():
    nome = input("Nome do produto: ")
    preco = float(input("Preço: R$ "))
    estoque = int(input("Quantidade em estoque: "))
    categoria = input("Categoria: ")
    
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO produtos (nome, preco, estoque, categoria) VALUES (?,?,?,?)",
                  (nome, preco, estoque, categoria))
    conn.commit()
    conn.close()
    print("✅ Produto cadastrado!")

def listar_produtos():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome, preco, estoque, categoria FROM produtos")
    produtos = cursor.fetchall()
    conn.close()
    
    if not produtos:
        print("Nenhum produto cadastrado.")
        return
    
    print(tabulate(produtos, headers=["ID", "Nome", "Preço", "Estoque", "Categoria"], tablefmt="grid"))

# ====================== VENDAS ======================
def realizar_venda():
    conn = conectar()
    cursor = conn.cursor()
    
    # Listar clientes
    cursor.execute("SELECT id, nome FROM clientes")
    clientes = cursor.fetchall()
    if not clientes:
        print("Cadastre um cliente primeiro!")
        conn.close()
        return
    
    print("\nClientes:")
    for c in clientes:
        print(f"{c['id']} - {c['nome']}")
    
    cliente_id = int(input("\nID do cliente: "))
    
    venda_itens = []
    total = 0
    data = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    while True:
        listar_produtos()
        prod_id = input("\nID do produto (0 para finalizar): ")
        if prod_id == '0':
            break
            
        quantidade = int(input("Quantidade: "))
        
        cursor.execute("SELECT nome, preco, estoque FROM produtos WHERE id = ?", (prod_id,))
        produto = cursor.fetchone()
        
        if not produto:
            print("Produto não encontrado!")
            continue
        if produto['estoque'] < quantidade:
            print("Estoque insuficiente!")
            continue
            
        subtotal = produto['preco'] * quantidade
        total += subtotal
        
        venda_itens.append((prod_id, quantidade, produto['preco']))
        
        # Atualizar estoque temporariamente
        cursor.execute("UPDATE produtos SET estoque = estoque - ? WHERE id = ?", (quantidade, prod_id))
    
    if not venda_itens:
        print("Venda cancelada.")
        conn.close()
        return
    
    # Registrar venda
    cursor.execute("INSERT INTO vendas (data, cliente_id, total) VALUES (?,?,?)", 
                  (data, cliente_id, total))
    venda_id = cursor.lastrowid
    
    for item in venda_itens:
        cursor.execute("INSERT INTO itens_venda (venda_id, produto_id, quantidade, preco_unitario) VALUES (?,?,?,?)",
                      (venda_id, item[0], item[1], item[2]))
    
    conn.commit()
    conn.close()
    print(f"\n✅ Venda realizada com sucesso! Total: R$ {total:.2f}")

# ====================== RELATÓRIOS ======================
def relatorio_vendas():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT v.id, v.data, c.nome, v.total 
        FROM vendas v 
        LEFT JOIN clientes c ON v.cliente_id = c.id 
        ORDER BY v.data DESC
    """)
    vendas = cursor.fetchall()
    conn.close()
    
    print(tabulate(vendas, headers=["ID", "Data", "Cliente", "Total"], tablefmt="grid"))

def relatorio_estoque():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome, estoque, preco FROM produtos WHERE estoque > 0 ORDER BY estoque ASC")
    produtos = cursor.fetchall()
    conn.close()
    print(tabulate(produtos, headers=["ID", "Produto", "Estoque", "Preço"], tablefmt="grid"))

def produtos_mais_vendidos():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.nome, SUM(iv.quantidade) as total_vendido
        FROM itens_venda iv
        JOIN produtos p ON iv.produto_id = p.id
        GROUP BY p.id
        ORDER BY total_vendido DESC
        LIMIT 10
    """)
    produtos = cursor.fetchall()
    conn.close()
    print(tabulate(produtos, headers=["Produto", "Quantidade Vendida"], tablefmt="grid"))

# ====================== MENU ======================
def menu():
    criar_tabelas()
    while True:
        limpar_tela()
        print("="*50)
        print("          SISTEMA DE VENDAS - SisVenda")
        print("="*50)
        print("1. Cadastrar Cliente")
        print("2. Cadastrar Produto")
        print("3. Listar Produtos")
        print("4. Realizar Venda")
        print("5. Relatório de Vendas")
        print("6. Relatório de Estoque")
        print("7. Produtos Mais Vendidos")
        print("0. Sair")
        print("="*50)
        
        opcao = input("\nEscolha uma opção: ")
        
        if opcao == '1':
            cadastrar_cliente()
        elif opcao == '2':
            cadastrar_produto()
        elif opcao == '3':
            listar_produtos()
        elif opcao == '4':
            realizar_venda()
        elif opcao == '5':
            relatorio_vendas()
        elif opcao == '6':
            relatorio_estoque()
        elif opcao == '7':
            produtos_mais_vendidos()
        elif opcao == '0':
            print("👋 Até logo!")
            break
        else:
            print("Opção inválida!")
        
        input("\nPressione ENTER para continuar...")

if __name__ == "__main__":
    # Instalar tabulate se necessário
    try:
        from tabulate import tabulate
    except ImportError:
        print("Instalando tabulate...")
        import subprocess
        subprocess.check_call(["pip", "install", "tabulate"])
    
    menu()

# sisvendaimport sqlite3

# Conexão com o banco de dados
conn = sqlite3.connect("sisvenda.db")
cursor = conn.cursor()

# Criação das tabelas
cursor.execute("""
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario TEXT UNIQUE NOT NULL,
    senha TEXT NOT NULL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS clientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    email TEXT,
    telefone TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS produtos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    preco REAL NOT NULL,
    estoque INTEGER NOT NULL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS vendas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id INTEGER,
    produto_id INTEGER,
    quantidade INTEGER,
    total REAL,
    FOREIGN KEY(cliente_id) REFERENCES clientes(id),
    FOREIGN KEY(produto_id) REFERENCES produtos(id)
)
""")

conn.commit()

# Funções do sistema
def cadastrar_usuario(usuario, senha):
    try:
        cursor.execute("INSERT INTO usuarios (usuario, senha) VALUES (?, ?)", (usuario, senha))
        conn.commit()
        print("Usuário cadastrado com sucesso!")
    except sqlite3.IntegrityError:
        print("Usuário já existe.")

def login(usuario, senha):
    cursor.execute("SELECT * FROM usuarios WHERE usuario=? AND senha=?", (usuario, senha))
    return cursor.fetchone() is not None

def cadastrar_cliente(nome, email, telefone):
    cursor.execute("INSERT INTO clientes (nome, email, telefone) VALUES (?, ?, ?)", (nome, email, telefone))
    conn.commit()
    print("Cliente cadastrado com sucesso!")

def cadastrar_produto(nome, preco, estoque):
    cursor.execute("INSERT INTO produtos (nome, preco, estoque) VALUES (?, ?, ?)", (nome, preco, estoque))
    conn.commit()
    print("Produto cadastrado com sucesso!")

def registrar_venda(cliente_id, produto_id, quantidade):
    cursor.execute("SELECT preco, estoque FROM produtos WHERE id=?", (produto_id,))
    produto = cursor.fetchone()
    if produto:
        preco, estoque = produto
        if quantidade <= estoque:
            total = preco * quantidade
            cursor.execute("INSERT INTO vendas (cliente_id, produto_id, quantidade, total) VALUES (?, ?, ?, ?)",
                           (cliente_id, produto_id, quantidade, total))
            cursor.execute("UPDATE produtos SET estoque = estoque - ? WHERE id=?", (quantidade, produto_id))
            conn.commit()
            print(f"Venda registrada! Total: R$ {total:.2f}")
        else:
            print("Estoque insuficiente.")
    else:
        print("Produto não encontrado.")

# Exemplo de uso
if __name__ == "__main__":
    cadastrar_usuario("admin", "1234")
    if login("admin", "1234"):
        print("Login realizado com sucesso!")
        cadastrar_cliente("João Silva", "joao@email.com", "99999-9999")
        cadastrar_produto("Notebook", 3500.00, 10)
        registrar_venda(1, 1, 2)
    else:
        print("Usuário ou senha inválidos.")


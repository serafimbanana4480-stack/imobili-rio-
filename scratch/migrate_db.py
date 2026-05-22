import sqlite3
import os

db_path = 'data/db/realestate.db'
if not os.path.exists(db_path):
    print(f"Erro: Base de dados não encontrada em {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

columns_to_add = [
    ('is_active', 'INTEGER DEFAULT 1'),
    ('is_duplicate', 'INTEGER DEFAULT 0'),
    ('duplicate_of_id', 'TEXT')
]

for col_name, col_type in columns_to_add:
    try:
        cursor.execute(f"ALTER TABLE clean_listings ADD COLUMN {col_name} {col_type}")
        print(f"Coluna {col_name} adicionada.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print(f"Coluna {col_name} já existe.")
        else:
            print(f"Erro ao adicionar {col_name}: {e}")

conn.commit()
conn.close()
print("Migração concluída.")

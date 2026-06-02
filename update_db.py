import sqlite3

def add_column(conn, table, column, type):
    try:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {type}")
        print(f"Added {column}")
    except sqlite3.OperationalError as e:
        print(f"Skipped {column}: {e}")

conn = sqlite3.connect('praktyki.db')
columns = [
    ('instytucja_1', 'VARCHAR(255)'),
    ('okres_1', 'VARCHAR(100)'),
    ('instytucja_2', 'VARCHAR(255)'),
    ('okres_2', 'VARCHAR(100)'),
    ('komisja_2', 'VARCHAR(255)'),
    ('komisja_3', 'VARCHAR(255)'),
    ('rola_3', 'VARCHAR(255)'),
    ('komisja_4', 'VARCHAR(255)'),
    ('rola_4', 'VARCHAR(255)'),
    ('pytanie_1', 'TEXT'),
    ('ocena_czastkowa_1', 'FLOAT'),
    ('pytanie_2', 'TEXT'),
    ('ocena_czastkowa_2', 'FLOAT'),
    ('pytanie_3', 'TEXT'),
    ('ocena_czastkowa_3', 'FLOAT'),
    ('ocena_e', 'FLOAT'),
    ('ocena_k_slownie', 'VARCHAR(255)')
]

for col, typ in columns:
    add_column(conn, 'protokol', col, typ)

conn.commit()
conn.close()

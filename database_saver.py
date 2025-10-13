import json
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import execute_values
import os

load_dotenv()

db_params = {
    'dbname': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT')
}

create_table_script = '''
CREATE TABLE IF NOT EXISTS fatwas (
    id SERIAL PRIMARY KEY,
    url TEXT UNIQUE,
    question TEXT,
    answer TEXT,
    category VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
'''

insert_entry_script = '''
INSERT INTO fatwas (url, question, answer, category)
VALUES %s
ON CONFLICT (url) DO NOTHING;
'''

create_index_script = '''
CREATE INDEX IF NOT EXISTS idx_fatwas_category ON fatwas(category);
'''

with open('./fatwa_data/raw_fatwas.json', 'r', encoding='utf-8') as f:
    fatwas = json.load(f)

# try:
#     with psycopg2.connect(**db_params) as conn:
#         with conn.cursor() as cur:

#             cur.execute(create_table_script)
            
#             # Indexing
#             cur.execute(create_index_script)

#             # Insertion
#             execute_values(cur, insert_entry_script, [
#                 (f.get('url'), f.get('question'), f.get('answer'), f.get('category'))
#                 for f in fatwas
#                 if f.get('url') and f.get('question') and f.get('answer')
#             ])

#             conn.commit()
#             print(f'Successfully loaded {len(fatwas)} fatwas into database')
 
# except Exception as e:
#     print(f'Error: {e}')


# ====== check data is saved ==========

conn = psycopg2.connect(
    dbname=os.getenv('DB_NAME'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    host=os.getenv('DB_HOST'),
    port=os.getenv('DB_PORT')
)
cur = conn.cursor()
cur.execute("SELECT question FROM fatwas LIMIT 5;")
for row in cur.fetchall():
    print(row[0])
import psycopg2

# URL do seu banco ANTIGO do Render (onde estão os seus dados e o domingo passado)
url_antiga = "postgresql://db_church_lbz8_user:C0YsHYUOPMfyMmfeUiymDJKd9Q9XlIZF@dpg-d9hamd58nd3s73cknvug-a.oregon-postgres.render.com/db_church_lbz8"

# URL do seu banco NOVO (Supabase)
url_nova = "postgresql://postgres.wwgecbevcghkntanigls:WAaNlFHr87B5XEX4@aws-0-sa-east-1.pooler.supabase.com:5432/postgres"

print("Conectando aos bancos...")
conn_antiga = psycopg2.connect(url_antiga)
conn_nova = psycopg2.connect(url_nova)

cur_antiga = conn_antiga.cursor()
cur_nova = conn_nova.cursor()

# 1. Limpa o banco novo para evitar duplicidade ou dados bagunçados
print("Limpando dados atuais do Supabase...")
cur_nova.execute("DELETE FROM attendances;")
cur_nova.execute("DELETE FROM events;")
conn_nova.commit()

# 2. Copia os eventos originais do banco antigo (trazendo de volta o domingo passado)
print("Restaurando eventos originais (incluindo o domingo passado)...")
cur_antiga.execute("SELECT * FROM events;")
eventos = cur_antiga.fetchall()
if eventos:
    cur_antiga.execute("SELECT column_name FROM information_schema.columns WHERE table_schema='public' AND table_name='events';")
    cols = [r[0] for r in cur_antiga.fetchall()]
    cols_str = ", ".join([f'"{c}"' for c in cols])
    placeholders = ", ".join(["%s"] * len(cols))
    for ev in eventos:
        cur_nova.execute(f"INSERT INTO events ({cols_str}) VALUES ({placeholders}) ON CONFLICT DO NOTHING;", ev)
    conn_nova.commit()

# 3. Copia todas as presenças antigas reais
print("Restaurando as presenças...")
cur_antiga.execute("SELECT * FROM attendances;")
presencas = cur_antiga.fetchall()
if presencas:
    cur_antiga.execute("SELECT column_name FROM information_schema.columns WHERE table_schema='public' AND table_name='attendances';")
    cols = [r[0] for r in cur_antiga.fetchall()]
    cols_str = ", ".join([f'"{c}"' for c in cols])
    placeholders = ", ".join(["%s"] * len(cols))
    for pr in presencas:
        cur_nova.execute(f"INSERT INTO attendances ({cols_str}) VALUES ({placeholders}) ON CONFLICT DO NOTHING;", pr)
    conn_nova.commit()

# 4. Copia usuários e membros para garantir que nada falta
for tabela in ['users', 'members', 'notices']:
    try:
        cur_antiga.execute(f"SELECT * FROM {tabela};")
        linhas = cur_antiga.fetchall()
        if linhas:
            cur_antiga.execute(f"SELECT column_name FROM information_schema.columns WHERE table_schema='public' AND table_name='{tabela}';")
            cols = [r[0] for r in cur_antiga.fetchall()]
            cols_str = ", ".join([f'"{c}"' for c in cols])
            placeholders = ", ".join(["%s"] * len(cols))
            for linha in linhas:
                cur_nova.execute(f"INSERT INTO {tabela} ({cols_str}) VALUES ({placeholders}) ON CONFLICT DO NOTHING;", linha)
            conn_nova.commit()
    except Exception as e:
        print(f"Aviso na tabela {tabela}: {e}")

cur_antiga.close()
cur_nova.close()
conn_antiga.close()
conn_nova.close()

print("\nTudo pronto! Seus dados e o domingo passado foram restaurados com sucesso.")
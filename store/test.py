import psycopg2

try:
    conn = psycopg2.connect(
        host="localhost",
        database="iot_db",
        user="roma",
        password="tobeor",
        port="5432"
    )
    print("З'єднання успішне!")
    
    cur = conn.cursor()
    cur.execute('SELECT version()')
    db_version = cur.fetchone()
    print(f"Версія PostgreSQL: {db_version}")
    
except Exception as e:
    print(f"Помилка: {e}")
finally:
    if 'conn' in locals():
        conn.close()
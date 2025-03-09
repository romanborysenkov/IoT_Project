import psycopg2
from datetime import datetime

def test_connection():
    try:
        # Підключення до бази даних
        conn = psycopg2.connect(
            host="localhost",  # або "postgres_db" якщо запускаєте з Docker
            database="iot_db",
            user="postgres",
            password="tobeor",
            port="5432"
        )
        print("Підключення успішне!")
        
        # Створюємо курсор
        cur = conn.cursor()
        
        # Перевіряємо версію PostgreSQL
        cur.execute('SELECT version()')
        db_version = cur.fetchone()
        print(f"Версія PostgreSQL: {db_version[0]}")
        
        # Перевіряємо таблицю
        cur.execute('SELECT * FROM processed_agent_data LIMIT 5')
        rows = cur.fetchall()
        print("\nПерші 5 записів з таблиці:")
        for row in rows:
            print(row)
            
    except Exception as e:
        print(f"Помилка: {e}")
    finally:
        # Закриваємо підключення
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()
            print("\nПідключення закрито")

if __name__ == "__main__":
    test_connection() 
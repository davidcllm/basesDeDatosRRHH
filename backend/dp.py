import pymysql
import os
from werkzeug.security import generate_password_hash

def get_connection():
    """Establece y retorna una conexión a la base de datos usando variables de entorno con valores por defecto."""
    return pymysql.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "admin"),
        password=os.getenv("DB_PASS", "admin123"),
        database=os.getenv("DB_NAME", "mydb"),
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False
    )

def create_user_in_db(email, password, rol):
    """
    Hashea la contraseña e inserta email/password_hash/rol en la tabla USUARIO.
    Retorna True si la inserción es exitosa, False en caso contrario.
    """
    password_hash = generate_password_hash(password)
    
    cnx = None
    cursor = None
    try:
        cnx = get_connection()
        cursor = cnx.cursor()
        
        sql = "INSERT INTO USUARIO (email, password_hash, rol) VALUES (%s, %s, %s)"
        cursor.execute(sql, (email, password_hash, rol))
        
        cnx.commit()
        return True
    except pymysql.IntegrityError as e:
        # email duplicado u otras violaciones de integridad
        print(f"Error de integridad al crear usuario: {e}")
        if cnx:
            cnx.rollback()
        return False
    except Exception as e:
        print(f"Error al crear usuario: {e}")
        if cnx:
            cnx.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if cnx:
            cnx.close()
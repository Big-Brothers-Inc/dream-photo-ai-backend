import psycopg2
import os
from dotenv import load_dotenv
from contextlib import contextmanager

connection = None
load_dotenv()


def init_connection():
    global connection
    if connection is None:
        try:
            connection = psycopg2.connect(
                database=os.environ.get("POSTGRES_DB"),
                user=os.environ.get("POSTGRES_USER"),
                password=os.environ.get("POSTGRES_PASSWORD"),
                host="db",
                port=os.environ.get("POSTGRES_PORT")
            )
            print("Connected to the PostgreSQL database successfully.")
        except (Exception, psycopg2.Error) as error:
            print("Error while connecting to PostgreSQL:", error)


def close_connection():
    global connection
    if connection is not None:
        connection.close()
        print("Database connection closed.")
        connection = None


@contextmanager
def get_cursor():
    """
    Yields a cursor from the global connection. Automatically closes it after use.
    Ensures the connection is initialized before use.
    """
    global connection
    if connection is None:
        init_connection()

    cursor = connection.cursor()
    try:
        yield cursor
        connection.commit()
    except Exception as e:
        connection.rollback()
        print("Error during DB operation:", e)
        raise
    finally:
        cursor.close()

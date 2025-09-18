# myapp/db_utils.py

from django.db import connections
from administration.thread_local import get_current_service


class Db:
    @staticmethod
    def get_connection(database_alias=None):
        """
        Get the database connection based on the alias provided.
        Defaults to thread-local current_service, or 'default'.
        """
        if database_alias is None:
            database_alias = get_current_service() or 'default'
        return connections[database_alias]

    @staticmethod
    def close_connection(database_alias=None):
        """
        Close the database connection if it's open.
        Defaults to thread-local current_service, or 'default'.
        """
        if database_alias is None:
            database_alias = get_current_service() or 'default'
        connection = connections[database_alias]
        connection.close()


def callproc(procedure_name, params=None, db=None):
    """
    Calls the specified stored procedure on the selected database.
    If db is not passed, it will use the thread-local current_service.
    """
    if db is None:
        db = get_current_service() or 'default'

    connection = Db.get_connection(db)
    try:
        fetched_data = []
        with connection.cursor() as cursor:
            cursor.callproc(procedure_name, params or [])
            for result in cursor.stored_results():
                fetched_data = result.fetchall()
        connection.commit()
        return fetched_data
    except Exception as e:
        connection.rollback()
        print(f"Error in callproc({procedure_name}): {e}")
        raise
    finally:
        Db.close_connection(db)


# # myapp/db_utils.py

# from django.db import connections

# class Db:
#     @staticmethod
#     def get_connection(database_alias='default'):
#         """
#         Get the database connection based on the alias provided ('default').
#         """
#         return connections["default"]

#     @staticmethod
#     def close_connection(database_alias='default'):
#         """
#         Close the database connection if it's open.
#         """
#         connection = connections["default"]
        
# def callproc(procedure_name, params=None):
#     """
#     Calls the specified stored procedure on the selected database.
#     """
#     connection = Db.get_connection()
#     try:
#         fetched_data=[]
#         with connection.cursor() as cursor:
#             cursor.callproc(procedure_name, params)
#             for result in cursor.stored_results():
#                 fetched_data = result.fetchall()
#             connection.commit()
#             return fetched_data
#     except Exception as e:
#         connection.rollback()
#         print(f"Error: {e}")
#         raise
#     finally:
#         Db.close_connection()


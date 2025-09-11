# yourapp/thread_local.py
import threading

_thread_locals = threading.local()

def set_current_service(service_name):
    """ Set the current database for thread-local storage. """
    _thread_locals.service = service_name

def get_current_service():
    """ Get the current database from thread-local storage. """
    return getattr(_thread_locals, 'service', 'default')




from .thread_local import get_current_service

class ServiceRouter:
    def db_for_read(self, model, **hints):
        if model._meta.app_label in ['auth', 'sessions']:
            return 'default'
        return get_current_service() or 'default'

    def db_for_write(self, model, **hints):
        if model._meta.app_label in ['auth', 'sessions']:
            return 'default'
        return get_current_service() or 'default'
    
    def allow_migrate(self, db, app_label, model_name=None, **hints):
        # allow all migrations in L01 for testing
        if db == 'L01':
            return True
        # normal logic for default
        if app_label in ['auth', 'sessions', 'contenttypes', 'admin']:
            return db == 'default'
        current_service = get_current_service() or 'default'
        return db == current_service

# class ServiceRouter:
#     def db_for_read(self, model, **hints):
#         if model._meta.app_label == 'sessions':
#             return 'default'
#         return get_current_service() or 'default'

#     def db_for_write(self, model, **hints):
#         if model._meta.app_label == 'sessions':
#             return 'default'
#         return get_current_service() or 'default'

#     def allow_migrate(self, db, app_label, model_name=None, **hints):
#         # System apps → always default
#         if app_label in ['auth', 'contenttypes', 'admin', 'sessions']:
#             return db == 'default'

#         # Your L01 app → only in L01_db
#         if app_label == 'L01':
#             return db == 'L01'

#         # Your L02 app → only in L02_db
#         if app_label == 'L02':
#             return db == 'L02'

#         # Everything else → default
#         return db == 'default'

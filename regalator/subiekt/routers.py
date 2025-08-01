class SubiektRouter:
    """
    Router that makes the 'subiekt' database read-only.
    All write operations will be prevented for models using this database.
    """
    
    def db_for_read(self, model, **hints):
        """Point all operations on subiekt models to 'subiekt' database for reading."""
        if hasattr(model, '_meta') and model._meta.app_label == 'subiekt':
            return 'subiekt'
        return None
    
    def db_for_write(self, model, **hints):
        """Prevent all write operations on subiekt models."""
        if hasattr(model, '_meta') and model._meta.app_label == 'subiekt':
            # Return None to prevent writes - Django will raise an error
            return None
        return None
    
    def allow_relation(self, obj1, obj2, **hints):
        """Allow relations if both objects are in the same database."""
        if (hasattr(obj1, '_meta') and obj1._meta.app_label == 'subiekt' and
            hasattr(obj2, '_meta') and obj2._meta.app_label == 'subiekt'):
            return True
        return None
    
    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """Prevent migrations on the subiekt database."""
        if app_label == 'subiekt':
            # Don't allow migrations on subiekt database
            return False
        return None 
def get_fully_qualified_name(obj):
    return obj.__module__ + "." + obj.__class__.__name__
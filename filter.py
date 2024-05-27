def to_dict(obj):
    if hasattr(obj, 'to_dict'):
        return obj.to_dict()
    else:
        return obj.__dict__
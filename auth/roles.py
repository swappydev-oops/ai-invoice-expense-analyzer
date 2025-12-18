def can_edit(role):
    return role in ["user", "admin"]

def can_view(role):
    return role in ["user", "client", "admin"]

"""
   Author: M I Schwartz

   Stores / retrieves a single "dict"
   The intent is for all unsettled transactions to be stored in it.
   A persistent version would back it up to and restore from a file or redis
   This could be the guts of a class if multiples stores are needed
"""
_DATASTORE = {}

def store(transaction):
    """Stores transaction by approval_code"""
    result = True
    if "approval_code" in transaction:
        _DATASTORE[transaction["approval_code"]] = transaction
    else:
        print("Cannot store unapproved transaction")
        result = False

    return result

def settle(approval_code):
    """Remove approved transaction once settled"""
    if approval_code in _DATASTORE:
        result = _DATASTORE[approval_code]
        _DATASTORE.pop(approval_code, None)
    else:
        result = {"failure_code": 404, "failure_message": "No such unsettled transaction"}
    return result

def size():
    """Return the number of items awaiting settlement"""
    return len(_DATASTORE)

def get_unsettled_keys():
    """Returns a list of the keys of unsettled items"""
    result = []
    for key in _DATASTORE:
        result.append(key)
    return result

def get_unsettled():
    """Returns the full transaction for unsettled items"""
    result = []
    for key in _DATASTORE:
        result.append(_DATASTORE[key])
    return result

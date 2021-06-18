@staticmethod
def get_key_by_value(value, dict_to_search):
    for dkey, dvalue in dict_to_search.item():
        if dvalue == value:
            return dkey
    return -1

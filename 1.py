import hashlib
def hash_code(s, salt='nemo'):
    md5 = hashlib.md5()
    s += salt
    mima = md5.update(s.encode('utf-8'))
    print(mima)
if __name__ == '__main__':
    s=123
    print(type(s))
    a=str(s)
    print(type(a))
    hash_code(a)
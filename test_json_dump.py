import json

a = 'my string with "double quotes" blablabla'
print(json.dumps(a))

b = 'my string with double\_quotes blablabla'
print(json.dumps(b))

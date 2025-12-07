from database import AttrDict, _node_to_dict, _record_to_dict, safe_run

# Test 1: Basic AttrDict with properties
d = AttrDict({'username': 'admin', 'email': 'admin@test.com'})
print(f"Test 1 - Basic AttrDict:")
print(f"  type(d) = {type(d)}")
print(f"  d['username'] = {d['username']}")
print(f"  d.username = {d.username}")
print(f"  Accessing first char: {d.username[0]}")
print()

# Test 2: Check hasattr
print(f"Test 2 - hasattr checks:")
print(f"  hasattr(d, 'username') = {hasattr(d, 'username')}")
print(f"  'username' in d = {'username' in d}")
print()

# Test 3: Empty AttrDict
e = AttrDict()
print(f"Test 3 - Empty AttrDict:")
print(f"  len(e) = {len(e)}")
print(f"  dict(e) = {dict(e)}")
try:
    print(f"  e.username = {e.username}")
except AttributeError as ex:
    print(f"  AttributeError: {ex}")
print()

# Test 4: Nested structure like _record_to_dict returns
record = AttrDict({'u': AttrDict({'username': 'admin', 'email': 'admin@test.com'})})
print(f"Test 4 - Nested structure:")
print(f"  record['u'] = {record['u']}")
print(f"  record['u'].username = {record['u'].username}")
print()

# Test 5: What does our code actually do?
users = [record['u'] for record in [record]]
print(f"Test 5 - What our code does:")
print(f"  users = {users}")
print(f"  users[0] = {users[0]}")
print(f"  users[0].username = {users[0].username}")
print(f"  users[0].username[0].upper() = {users[0].username[0].upper()}")

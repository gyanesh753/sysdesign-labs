# lab2_schema_evolution.py - DDIA Ch 5: old and new code reading each other's data during a rolling upgrade
from lab1_encodings import decode_ordered, decode_tagged, encode_ordered, encode_tagged

V1 = [(1, 'name', 'string'), (2, 'visits', 'int'), (3, 'interests', 'strings')]
V2 = V1 + [(4, 'email', 'string')]                      # new optional field, NEW tag number

old_bytes = encode_tagged({'name': 'Amara', 'visits': 7, 'interests': ['chess']}, V1)
new_bytes = encode_tagged({'name': 'Bilal', 'visits': 3, 'interests': [], 'email': 'bilal@example.com'}, V2)

print('1. BACKWARD compatibility: new code reads old data')
record, _ = decode_tagged(old_bytes, V2)
record.setdefault('email', None)                         # the field is simply absent, so the reader supplies a default
print(f'   {record}')

print('\n2. FORWARD compatibility: old code reads new data')
record, unknown = decode_tagged(new_bytes, V1)
print(f'   {record}   (skipped {len(unknown)} bytes it did not understand)')

print('\n3. The trap: old code reads a new record, changes it, and writes it back')
record['visits'] += 1
lossy = encode_tagged(record, V1)                        # re-encodes only the fields it knows
careful = encode_tagged(record, V1) + unknown            # keeps the unknown bytes and writes them back
print(f'   re-encoded from known fields only -> new code sees email = {decode_tagged(lossy, V2)[0].get("email")!r}   <- silently lost')
print(f'   unknown bytes preserved           -> new code sees email = {decode_tagged(careful, V2)[0].get("email")!r}')

print('\n4. Breaking changes')
BAD_REUSE = [(1, 'name', 'string'), (2, 'nickname', 'string'), (3, 'interests', 'strings')]   # tag 2 reused with another type
try:
    decode_tagged(old_bytes, BAD_REUSE)
except ValueError as e:
    print(f'   reusing tag 2 for a different field: {e}')
record, _ = decode_tagged(old_bytes, V2)
print(f'   making the new field required: old record has email? {"email" in record}  -> every old record would be rejected')

print('\n5. No tags: the reader needs the writer\'s schema')
WRITER = [('name', 'string'), ('visits', 'int'), ('interests', 'strings')]
READER = [('name', 'string'), ('email', 'string'), ('visits', 'int')]      # reader added email, dropped interests, reordered
data = encode_ordered({'name': 'Amara', 'visits': 7, 'interests': ['chess']}, WRITER)
try:
    wrong = decode_ordered(data, READER)
    print(f'   decoded with the reader\'s schema alone: {wrong}   <- nonsense, and no error')
except Exception as e:
    print(f'   decoded with the reader\'s schema alone: fails with {type(e).__name__}')
written = decode_ordered(data, WRITER)                                      # decode with the writer's schema...
DEFAULTS = {'email': None}
resolved = {name: written.get(name, DEFAULTS.get(name)) for name, _ in READER}   # ...then match fields BY NAME
print(f'   decoded with writer schema, then resolved by name: {resolved}')

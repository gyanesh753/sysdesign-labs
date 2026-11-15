# lab1_encodings.py - DDIA Ch 5: one record encoded three ways: JSON text, tagged binary, schema-ordered binary
import json

# ---- shared building blocks -------------------------------------------------------------------

def varint(n):
    """Variable-length integer: 7 bits per byte, top bit set on every byte except the last."""
    out = bytearray()
    while True:
        byte, n = n & 0x7F, n >> 7
        out.append(byte | (0x80 if n else 0))
        if not n:
            return bytes(out)


def read_varint(buf, pos):
    result = shift = 0
    while True:
        byte = buf[pos]
        pos += 1
        result |= (byte & 0x7F) << shift
        if not byte & 0x80:
            return result, pos
        shift += 7


def text(s):
    data = s.encode()
    return varint(len(data)) + data


# ---- style 1: every value carries a numeric field tag (the Protocol Buffers idea) ---------------
# schema: list of (tag, name, type) where type is 'int', 'string' or 'strings' (a repeated string)

def encode_tagged(record, schema):
    out = bytearray()
    for tag, name, kind in schema:
        if name not in record:
            continue
        if kind == 'int':
            out += varint(tag << 3 | 0) + varint(record[name])            # wire type 0 = varint
        else:
            for item in (record[name] if kind == 'strings' else [record[name]]):
                out += varint(tag << 3 | 2) + text(item)                   # wire type 2 = length-prefixed
    return bytes(out)


def decode_tagged(buf, schema):
    """Returns (record, unknown) where unknown holds the raw bytes of fields this schema has never heard of."""
    by_tag = {tag: (name, kind) for tag, name, kind in schema}
    record, unknown, pos = {}, bytearray(), 0
    while pos < len(buf):
        start = pos
        key, pos = read_varint(buf, pos)
        tag, wire = key >> 3, key & 7
        if wire == 0:
            value, pos = read_varint(buf, pos)
        else:
            length, pos = read_varint(buf, pos)
            value, pos = buf[pos:pos + length].decode(), pos + length
        if tag not in by_tag:
            unknown += buf[start:pos]          # the wire type told us how many bytes to skip
            continue
        name, kind = by_tag[tag]
        if (kind == 'int') != (wire == 0):
            raise ValueError(f'field {name!r} (tag {tag}): expected {kind}, the bytes hold something else')
        if kind == 'strings':
            record.setdefault(name, []).append(value)
        else:
            record[name] = value
    return record, bytes(unknown)


# ---- style 2: no tags at all; values in schema order (the Avro idea) ----------------------------
# schema: list of (name, type). The reader MUST know the exact schema the writer used.

def encode_ordered(record, schema):
    out = bytearray()
    for name, kind in schema:
        if kind == 'int':
            out += varint(record[name])
        elif kind == 'string':
            out += text(record[name])
        else:
            out += varint(len(record[name])) + b''.join(text(i) for i in record[name])
    return bytes(out)


def decode_ordered(buf, schema):
    record, pos = {}, 0

    def read_text():
        nonlocal pos
        length, pos = read_varint(buf, pos)
        value = buf[pos:pos + length].decode()
        pos += length
        return value

    for name, kind in schema:
        if kind == 'int':
            record[name], pos = read_varint(buf, pos)
        elif kind == 'string':
            record[name] = read_text()
        else:
            count, pos = read_varint(buf, pos)
            record[name] = [read_text() for _ in range(count)]
    return record


TAGGED = [(1, 'name', 'string'), (2, 'visits', 'int'), (3, 'interests', 'strings')]
ORDERED = [('name', 'string'), ('visits', 'int'), ('interests', 'strings')]

if __name__ == '__main__':
    record = {'name': 'Amara', 'visits': 42000, 'interests': ['hiking', 'chess']}
    as_json = json.dumps(record, separators=(',', ':')).encode()
    tagged = encode_tagged(record, TAGGED)
    ordered = encode_ordered(record, ORDERED)
    assert decode_tagged(tagged, TAGGED)[0] == record and decode_ordered(ordered, ORDERED) == record

    print(f'record: {record}\n')
    print(f'{"encoding":<34}{"bytes":>6}   field names in the data?')
    print(f'{"JSON text":<34}{len(as_json):>6}   yes, spelled out in every record')
    print(f'{"binary with field tags":<34}{len(tagged):>6}   no, a 1-byte tag number instead')
    print(f'{"binary in schema order, no tags":<34}{len(ordered):>6}   no, nothing at all: position is everything')
    print(f'\ntagged : {tagged.hex(" ")}')
    print(f'ordered: {ordered.hex(" ")}')
    print(f'\nfirst tagged byte 0x{tagged[0]:02x} = tag {tagged[0] >> 3}, wire type {tagged[0] & 7} (length-prefixed), then length {tagged[1]}, then {tagged[2:7]!r}')
    print(f'42000 as a varint takes {len(varint(42000))} bytes: {varint(42000).hex(" ")}; as JSON digits it takes 5')

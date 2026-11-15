## Goal

Encode a record by hand so the bytes stop being mysterious, then break and fix compatibility the way a real rolling upgrade would.

Both labs are plain Python with no dependencies and run instantly. Lab 2 imports the codec from lab 1.

## Lab 1: three encodings of one record

```bash
python lab1_encodings.py
```

The script implements variable-length integers and two small binary codecs: one that tags every value with a field number, and one that writes values in schema order with nothing else.

**What you should observe**

- JSON takes 62 bytes, the tagged encoding 26, and the schema-ordered encoding 23.
- The three bytes that separate the two binary encodings are the three field tags. JSON's extra size is mostly field names and punctuation.
- In the hex dump you can read the tagged encoding by eye: a byte holding the tag and type, a length, then the text.
- The number 42000 takes 3 bytes as a variable-length integer and 5 as JSON digits.

**Try**

1. Encode a record with 100 interests. How does the gap between the three encodings change, and why?
2. Add a negative number. What does the variable-length integer do with it, and how do real formats avoid the problem?

## Lab 2: a rolling upgrade

```bash
python lab2_schema_evolution.py
```

Version 2 of the schema adds an optional `email` field with a new tag number. The script then plays out each situation that arises while both versions are running.

**What you should observe**

1. New code reads an old record and fills in a default for the missing field.
2. Old code reads a new record and skips 19 bytes it does not understand.
3. Old code updates that record and writes it back. Re-encoding from known fields loses the email silently; keeping the unknown bytes preserves it.
4. Reusing a tag number for a field of another type makes old data fail to decode. Making the new field required would reject every old record.
5. With the tag-free encoding, decoding with the wrong schema fails, and decoding with the writer's schema then matching by name works even though the reader reordered, added and dropped fields.

**Try**

1. In step 4, reuse tag 2 for a field of the *same* type (another integer). Does anything fail? Why is that worse than an error?
2. In step 5, change the reader's schema so it happens to have the same types in the same positions but different names. What does decoding with the reader's schema alone return?

## Write up in NOTES.md

Record the three sizes from lab 1 and what each step of lab 2 printed. Then answer: name one place in a system you know where old and new code read the same data, and which direction of compatibility is most at risk there.

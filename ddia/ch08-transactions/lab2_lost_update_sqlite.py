# lab2_lost_update_sqlite.py - DDIA Ch 8: a real database, four threads, one counter: losing updates and three ways not to
import os
import sqlite3
import tempfile
import threading
import time

THREADS, INCREMENTS = 4, 150
EXPECTED = THREADS * INCREMENTS


def connect(path):
    con = sqlite3.connect(path, timeout=30, isolation_level=None)      # autocommit; we say BEGIN ourselves when we want one
    con.execute('PRAGMA journal_mode=WAL')
    return con


def read_then_write(con):
    """Read-modify-write in application code, no protection."""
    (value,) = con.execute('SELECT value FROM counter').fetchone()
    time.sleep(0.0002)                                                 # the application "thinks"
    con.execute('UPDATE counter SET value=?', (value + 1,))
    return 0


def atomic_update(con):
    """Let the database do the read and the write as one operation."""
    con.execute('UPDATE counter SET value = value + 1')
    return 0


def explicit_lock(con):
    """Take the write lock BEFORE reading, so nobody else can read-then-write in between."""
    con.execute('BEGIN IMMEDIATE')
    (value,) = con.execute('SELECT value FROM counter').fetchone()
    time.sleep(0.0002)
    con.execute('UPDATE counter SET value=?', (value + 1,))
    con.execute('COMMIT')
    return 0


def compare_and_set(con):
    """Write only if the row is still the version we read; otherwise start over."""
    retries = 0
    while True:
        value, version = con.execute('SELECT value, version FROM counter').fetchone()
        time.sleep(0.0002)
        changed = con.execute('UPDATE counter SET value=?, version=version+1 WHERE version=?', (value + 1, version)).rowcount
        if changed:
            return retries
        retries += 1


print(f'{THREADS} threads x {INCREMENTS} increments, expected final value {EXPECTED}\n')
print(f'{"approach":<34}{"final":>7}{"lost":>7}{"retries":>9}{"seconds":>9}')
with tempfile.TemporaryDirectory() as tmp:
    for label, fn in [('read, then write (no protection)', read_then_write), ('atomic UPDATE value = value + 1', atomic_update),
                      ('explicit lock (BEGIN IMMEDIATE)', explicit_lock), ('compare-and-set with a version', compare_and_set)]:
        path = os.path.join(tmp, f'{fn.__name__}.db')
        setup = connect(path)
        setup.execute('CREATE TABLE counter(value INT, version INT)')
        setup.execute('INSERT INTO counter VALUES (0, 0)')
        retries = []

        def worker():
            con = connect(path)
            retries.append(sum(fn(con) for _ in range(INCREMENTS)))
            con.close()

        start = time.perf_counter()
        threads = [threading.Thread(target=worker) for _ in range(THREADS)]
        [t.start() for t in threads]
        [t.join() for t in threads]
        (final,) = setup.execute('SELECT value FROM counter').fetchone()
        setup.close()
        print(f'{label:<34}{final:>7}{EXPECTED - final:>7}{sum(retries):>9}{time.perf_counter() - start:>9.2f}')

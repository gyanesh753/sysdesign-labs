# lab2_derived.py - DDIA Ch 1: system of record vs derived data (run lab1 first to create orders.db)
import sqlite3
import time

con = sqlite3.connect('orders.db')


def rebuild():
    con.execute('DROP TABLE IF EXISTS daily_revenue')
    t = time.perf_counter()
    con.execute('''CREATE TABLE daily_revenue AS
        SELECT date(ts) AS day, country, SUM(qty*price) AS revenue, COUNT(*) AS orders
        FROM orders GROUP BY day, country''')
    con.commit()
    print(f'rebuilt in {time.perf_counter() - t:.2f}s')


rebuild()

# Step 1: change the source. Is the derived table now stale?
row = con.execute('SELECT date(ts), country FROM orders WHERE order_id=42').fetchone()
con.execute('UPDATE orders SET qty = qty + 10 WHERE order_id=42')
con.commit()
truth = con.execute('SELECT SUM(qty*price) FROM orders WHERE date(ts)=? AND country=?', row).fetchone()
derived = con.execute('SELECT revenue FROM daily_revenue WHERE day=? AND country=?', row).fetchone()
print('source says', truth, '| derived says', derived)

# Step 2: incremental maintenance with a trigger
con.executescript('''
DROP TRIGGER IF EXISTS orders_upd;
CREATE TRIGGER orders_upd AFTER UPDATE OF qty, price ON orders
BEGIN
  UPDATE daily_revenue
  SET revenue = revenue - (OLD.qty*OLD.price) + (NEW.qty*NEW.price)
  WHERE day = date(NEW.ts) AND country = NEW.country;
END;''')
con.execute('UPDATE orders SET qty = qty + 1 WHERE order_id=42')
con.commit()
print('after trigger:', con.execute('SELECT revenue FROM daily_revenue WHERE day=? AND country=?', row).fetchone())
print('source now   :', con.execute('SELECT SUM(qty*price) FROM orders WHERE date(ts)=? AND country=?', row).fetchone())

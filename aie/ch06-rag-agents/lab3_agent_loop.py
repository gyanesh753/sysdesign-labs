# lab3_agent_loop.py - AIE Ch 6: an agent is a loop of plan, act and observe, and its errors compound
import random

random.seed(6)

# ---- the environment: four tools, one of which changes the world -------------------------------------
ORDERS = {'A-1001': {'customer': 'meera', 'item': 'kettle', 'paid': 1800}, 'A-1002': {'customer': 'meera', 'item': 'mug', 'paid': 350}}
PRICES = {'kettle': 1500, 'mug': 350}
refunds_sent = []


def find_orders(customer):
    return [k for k, v in ORDERS.items() if v['customer'] == customer]


def get_order(order_id):
    return ORDERS[order_id]


def list_price(item):
    return PRICES[item]


def send_refund(order_id, amount):                       # a WRITE action: it cannot be undone
    refunds_sent.append((order_id, amount))
    return f'refunded {amount} on {order_id}'


TOOLS = {'find_orders': find_orders, 'get_order': get_order, 'list_price': list_price, 'send_refund': send_refund}
WRITE_TOOLS = {'send_refund'}

print('PART A  one task, step by step')
print('  task: "Meera was overcharged for a kettle. Refund the difference."')
plan = [('find_orders', ('meera',)), ('get_order', ('A-1001',)), ('list_price', ('kettle',)), ('send_refund', ('A-1001', 300))]
for step, (tool, args) in enumerate(plan, 1):
    gate = '  [needs human approval: write action]' if tool in WRITE_TOOLS else ''
    print(f'  step {step}: call {tool}{args}{gate}\n          observation: {TOOLS[tool](*args)}')

print('\nPART B  errors compound: a model that is right 95% of the time per step')


def run_task(steps, step_accuracy, validate, retries):
    """Each step the model picks a tool and arguments. A mistake is either an INVALID call (unknown tool, wrong
    argument type), which a simple check can catch before running it, or a plausible but WRONG call, which it cannot."""
    for _ in range(steps):
        for attempt in range(retries + 1):
            if random.random() < step_accuracy:
                break                                        # correct call
            invalid = random.random() < 0.6                  # 60% of mistakes are the kind a validator can see
            if invalid and validate and attempt < retries:
                continue                                     # caught, reported back to the model, and tried again
            return False                                     # an undetected wrong step ruins the task
    return True


TRIALS = 20_000
print(f'  {"steps in the task":>18}{"no checks":>12}{"validate + 1 retry":>20}{"validate + 2 retries":>22}{"theory, no checks":>19}')
for steps in [1, 3, 5, 10, 20]:
    row = [sum(run_task(steps, 0.95, v, r) for _ in range(TRIALS)) / TRIALS for v, r in [(False, 0), (True, 1), (True, 2)]]
    print(f'  {steps:>18}{row[0]:>12.0%}{row[1]:>20.0%}{row[2]:>22.0%}{0.95 ** steps:>19.0%}')
print('  Checking each call and letting the model retry recovers the mistakes that can be detected.')
print('  The plausible-but-wrong calls remain, and they are why long tasks need evaluation of the final outcome too.')

print('\nPART C  how good does each step have to be?')
for target_steps in [5, 10, 20]:
    needed = 0.9 ** (1 / target_steps)
    print(f'  to finish a {target_steps}-step task 90% of the time, each step must be right {needed:.1%} of the time')

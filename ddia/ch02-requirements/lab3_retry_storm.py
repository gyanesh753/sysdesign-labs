# lab3_retry_storm.py - DDIA Ch 2: retry storm and metastable failure
import collections, heapq, random
random.seed(3)

def simulate(policy, seconds=70, dt=0.01):
    BASE, TIMEOUT, MAX_TRIES = 80, 1.0, 4        # base req/s, client timeout (s), attempts per request
    cap = lambda t: (35 if 20 <= t < 25 else 100) # server capacity (req/s): a 5-second slowdown at t=20
    queue, deadlines, retries = collections.deque(), collections.deque(), []
    budget, good, wasted, failed = 0.0, 0, 0, 0
    rows, t = [], 0.0
    next_row = 0
    while t < seconds:
        arrivals = [0] * (1 if random.random() < BASE * dt else 0)            # fresh requests (Bernoulli per tick)
        while retries and retries[0][0] <= t:
            arrivals.append(heapq.heappop(retries)[1])                          # retries that are due
        for attempt in arrivals:
            if policy == 'shed' and len(queue) > 40:                            # server rejects early when overloaded
                failed += 1
                if attempt + 1 < MAX_TRIES:
                    delay = 0.5 * 2 ** attempt * random.uniform(0.5, 1.5)
                    heapq.heappush(retries, (t + delay, attempt + 1))
                continue
            req = {'deadline': t + TIMEOUT, 'attempt': attempt, 'done': False}
            queue.append(req); deadlines.append(req)
        budget = min(budget + cap(t) * dt, 2.0)               # no banking of idle capacity
        while budget >= 1 and queue:
            budget -= 1
            r = queue.popleft()
            if t <= r['deadline']: r['done'] = True; good += 1
            else: wasted += 1                                                    # client already gave up: useless work
        while deadlines and deadlines[0]['deadline'] <= t:                       # client-side timeouts fire
            r = deadlines.popleft()
            if not r['done']:
                failed += 1
                if r['attempt'] + 1 < MAX_TRIES:
                    if policy == 'naive': delay = 0.0
                    else: delay = 0.5 * 2 ** r['attempt'] * random.uniform(0.5, 1.5)
                    heapq.heappush(retries, (t + delay, r['attempt'] + 1))
        if t >= next_row:
            rows.append((int(t), len(queue), good, wasted)); next_row += 5
        t += dt
    return rows

for policy in ['naive', 'backoff', 'shed']:
    print(f'\n=== policy: {policy}  (slowdown from t=20s to t=25s) ===')
    print('   t   queue   goodput_total  wasted_work_total')
    for t, q, g, w in simulate(policy):
        print(f'{t:>4} {q:>7} {g:>14} {w:>18}')

# lab1_replication_lag.py - DDIA Ch 6: asynchronous followers, replication lag, and the guarantees that hide it
import random

random.seed(6)
FOLLOWERS, USERS, STEPS = 3, 200, 20_000
MEAN_LAG = 30                         # a follower applies each write this many ticks after the leader, on average


def run(read_policy):
    leader = {}                                       # key -> version
    followers = [dict() for _ in range(FOLLOWERS)]
    pending = [[] for _ in range(FOLLOWERS)]          # per follower: (apply_at_tick, key, version), in log order
    last_apply = [0.0] * FOLLOWERS
    last_write_tick = {}                              # user -> tick of that user's latest write
    last_seen = {}                                    # user -> newest version of their own key they have been shown
    sticky = {u: random.randrange(FOLLOWERS) for u in range(USERS)}
    stats = dict(reads=0, stale_own_write=0, went_back_in_time=0, leader_reads=0)
    for tick in range(STEPS):
        for f in range(FOLLOWERS):                    # followers apply whatever is due
            while pending[f] and pending[f][0][0] <= tick:
                _, key, version = pending[f].pop(0)
                followers[f][key] = version
        user = random.randrange(USERS)
        if random.random() < 0.2:                     # write: goes to the leader, replicated asynchronously
            leader[user] = leader.get(user, 0) + 1
            last_write_tick[user] = tick
            for f in range(FOLLOWERS):
                # a follower applies the log strictly in order, so it can fall behind but never reorders writes
                last_apply[f] = max(last_apply[f], tick + random.expovariate(1 / MEAN_LAG))
                pending[f].append((last_apply[f], user, leader[user]))
        else:                                         # read your own profile
            stats['reads'] += 1
            recently_wrote = tick - last_write_tick.get(user, -10**9) < 5 * MEAN_LAG
            if read_policy == 'own writes from leader' and recently_wrote:
                seen = leader.get(user, 0)
                stats['leader_reads'] += 1
            elif read_policy == 'sticky follower':
                seen = followers[sticky[user]].get(user, 0)
            else:
                seen = followers[random.randrange(FOLLOWERS)].get(user, 0)
            if seen < leader.get(user, 0) and recently_wrote:
                stats['stale_own_write'] += 1         # you saved something and it is not there
            if seen < last_seen.get(user, 0):
                stats['went_back_in_time'] += 1       # you saw a newer value earlier than this older one
            last_seen[user] = max(seen, last_seen.get(user, 0))
    return stats


print(f'{FOLLOWERS} asynchronous followers, mean lag {MEAN_LAG} ticks, 20% writes\n')
print(f'{"read policy":<26}{"own write missing":>19}{"moved backward in time":>25}{"reads sent to leader":>23}')
for policy in ['any follower', 'sticky follower', 'own writes from leader']:
    s = run(policy)
    pct = lambda n: f'{100 * n / s["reads"]:.2f}%'
    print(f'{policy:<26}{pct(s["stale_own_write"]):>19}{pct(s["went_back_in_time"]):>25}{pct(s["leader_reads"]):>23}')

# lab3_two_phase_commit.py - DDIA Ch 8: two-phase commit, and what "in doubt" means when the coordinator dies
class Participant:
    def __init__(self, name, will_vote_yes=True):
        self.name, self.will_vote_yes = name, will_vote_yes
        self.state, self.locked = 'working', False

    def prepare(self):
        if not self.will_vote_yes:
            self.state = 'aborted'
            return False
        self.state, self.locked = 'prepared', True      # a promise: I WILL commit if told to, whatever happens. Locks stay held.
        return True

    def finish(self, decision):
        self.state, self.locked = decision, False

    def other_transaction_wants_the_row(self):
        return 'BLOCKED (row is locked by the in-doubt transaction)' if self.locked else 'ok'


class Coordinator:
    def __init__(self):
        self.log = []                                   # survives a crash, like a file on disk

    def run(self, participants, crash_at=None):
        votes = [p.prepare() for p in participants]     # phase 1: ask everyone
        if crash_at == 'before logging the decision':
            return 'crashed'
        decision = 'committed' if all(votes) else 'aborted'
        self.log.append(decision)                       # the commit point: once this is on disk the decision is final
        if crash_at == 'after logging the decision':
            return 'crashed'
        for p in participants:                          # phase 2: tell everyone
            if p.state == 'prepared':
                p.finish(decision)
        return decision

    def recover(self, participants):
        decision = self.log[-1] if self.log else 'aborted'      # nothing in the log means nothing was promised to anyone
        for p in participants:
            if p.state == 'prepared':
                p.finish(decision)
        return decision


def show(title, participants, outcome):
    print(f'{title}\n  coordinator: {outcome}')
    for p in participants:
        print(f'  {p.name:<10} state={p.state:<10} another transaction touching the same row: {p.other_transaction_wants_the_row()}')
    print()


ps = [Participant('orders'), Participant('payments')]
show('1. Everyone votes yes', ps, Coordinator().run(ps))

ps = [Participant('orders'), Participant('payments', will_vote_yes=False)]
show('2. One participant votes no', ps, Coordinator().run(ps))

for crash in ['after logging the decision', 'before logging the decision']:
    ps = [Participant('orders'), Participant('payments')]
    c = Coordinator()
    show(f'3. Coordinator crashes {crash}', ps, c.run(ps, crash_at=crash))
    print('   The participants cannot decide alone: if one commits and the other aborts, the data is inconsistent.')
    print('   They must wait, holding their locks, for as long as the coordinator is down.\n')
    show('   ...the coordinator restarts and reads its log', ps, c.recover(ps))

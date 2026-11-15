# lab2_end_to_end.py - DDIA Ch 13: "exactly once" has to hold from the user's click to the database, not just on one hop
import random

TRANSFERS, LOSS = 10_000, 0.15        # 15% of replies never reach the client


class Server:
    def __init__(self, dedupe_on):
        self.dedupe_on = dedupe_on        # None | 'connection' | 'request'
        self.moved = 0
        self.seen_on_connection = set()   # like TCP: forgets everything when the connection is replaced
        self.seen_request_ids = set()     # stored in the database, in the same transaction as the transfer

    def transfer(self, connection, packet_no, request_id, amount):
        if self.dedupe_on == 'connection' and (connection, packet_no) in self.seen_on_connection:
            return
        if self.dedupe_on == 'request' and request_id in self.seen_request_ids:
            return                        # already done: do nothing, just acknowledge again
        self.seen_on_connection.add((connection, packet_no))
        self.seen_request_ids.add(request_id)
        self.moved += amount


def run(dedupe_on):
    random.seed(13)
    server, connection, packet_no, retries = Server(dedupe_on), 0, 0, 0
    for request_id in range(TRANSFERS):   # the client invents one ID per thing the USER asked for
        packet_no += 1                    # every new request is a new packet on the current connection
        while True:
            server.transfer(connection, packet_no, request_id, 1)
            if random.random() > LOSS:
                break                     # the client saw the reply
            # No reply. Was the request lost, or only the reply? The client cannot tell, so it tries again.
            retries += 1
            if random.random() < 0.5:
                connection += 1           # half the time the connection has died: a new one starts numbering afresh
                packet_no = 1
            # (the other half: the same connection resends the very same packet, which the network layer recognizes)
    return server.moved, retries


print(f'{TRANSFERS:,} users each transfer 1 unit; {LOSS:.0%} of replies are lost and the client retries\n')
print(f'{"duplicate suppression":<46}{"units moved":>12}{"error":>8}')
for mode, label in [(None, 'none'), ('connection', 'per connection (what the network layer gives you)'), ('request', 'request ID checked by the database')]:
    moved, retries = run(mode)
    print(f'{label:<46}{moved:>12,}{moved - TRANSFERS:>+8,}')
print(f'\n({retries:,} retries in each run.)')
print('The network removes duplicate packets within one connection. It cannot know that a request on a NEW connection')
print('is a repeat of an earlier one. Only an ID that travels the whole way, checked where the money moves, can.')

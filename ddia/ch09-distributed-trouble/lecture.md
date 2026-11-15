## Partial failure

A program on one computer is fairly predictable. Either the machine works and the program gives the same result every time, or something is badly wrong and the whole thing stops. There is rarely anything in between.

A distributed system has an in-between, and lives in it. Some parts work while others are broken, and you may not be able to tell which. A message is sent and nothing comes back. This is **partial failure**, and what makes it hard is that it is nondeterministic: the same operation sometimes works and sometimes does not.

The useful attitude for this chapter is pessimism. Assume anything that can go wrong will, and then ask what can still be guaranteed. The reward is the ability to build a reliable system out of unreliable parts.

## Unreliable networks

The nodes of a distributed system share nothing except a network. When you send a request and get no reply, any of these may have happened: the request was lost, it is waiting in a queue, the other node crashed, the other node is paused and will answer later, or it did the work and the reply was lost.

From where you sit, these cases look identical. The only tool you have is a **timeout**: wait a while, then give up. Giving up tells you nothing about whether the request was carried out.

### Choosing a timeout

A long timeout means a long wait before a dead node is noticed, during which users see errors. A short timeout notices failures quickly but declares healthy nodes dead when they are only slow. A false alarm is costly: work is handed over and may be done twice, and if the node was slow because of overload, moving its work elsewhere can spread the overload.

There is no correct value, because network delays have no upper bound. Packets queue at a busy switch, at a busy machine before the application reads them, and in a virtual machine waiting for its turn on the CPU. A lost packet is retransmitted, which looks like delay to the application. The practical approach is to measure the real distribution of response times and choose with open eyes, or let the system adjust the timeout as conditions change.

### Why not make the network predictable

A traditional telephone call reserves a fixed amount of capacity along its whole route, so its delay is bounded. Data networks do not work that way, deliberately. Data traffic comes in bursts, and reserving capacity for each connection would waste most of it. Sharing the capacity gives far better use of the hardware, at the price of queueing. Variable delay is the result of a cost decision, not a law of physics.

## Unreliable clocks

Each machine has its own clock, driven by a quartz crystal that runs slightly fast or slow. Machines synchronize with time servers, but that correction travels over the same unreliable network.

### Two kinds of clock

- A **time-of-day clock** tells you the date and time. Because it is corrected to match a time server, it can jump forward or backward.
- A **monotonic clock** only ever moves forward. Its absolute value means nothing, but the difference between two readings is a trustworthy duration.

Use the monotonic clock to measure how long something took, including timeouts. Lab 2 shows a time-of-day clock reporting a negative duration for an operation that took a tenth of a second.

### How wrong clocks get

Drift of tens of seconds a day is possible without correction. Synchronization can only be as accurate as the network delay to the time server allows. A clock that is too far off may be reset abruptly. Leap seconds have crashed large systems. A virtual machine that is paused sees its clock leap forward when it resumes. And a misconfigured clock tends to go unnoticed, because most software keeps working while quietly producing wrong results.

### Timestamps for ordering events

It is tempting to order events across machines by timestamp, for example to decide which of two writes is the newer one. With last write wins, the write with the higher timestamp is kept.

The problem: if one node's clock is a few milliseconds behind another's, a write that truly happened later can carry an earlier timestamp and be discarded. No error is raised. The data is simply gone. Lab 2 measures how often this happens for a given skew.

A more honest view is that a clock reading is a range, not a point: the true time lies somewhere between an earliest and a latest value. Two events can only be ordered with certainty if their ranges do not overlap. A few systems expose that uncertainty and deliberately wait it out before committing, and keep it small with very accurate clocks in every datacentre. Where correct ordering matters and you do not have such clocks, use logical clocks, which chapter 10 covers.

### Process pauses

A running program can be stopped at any moment for an arbitrary length of time, and it does not notice. A garbage collector may halt every thread. A virtual machine may be suspended and moved. The operating system may be swapping memory to disk. A laptop lid may be closed.

So code like "check that I still hold the lease, then do the work" is unsafe. The pause can fall between the check and the work, and when the program resumes it believes no time has passed.

:::checkpoint[A node checks that its lease is valid for another 9 seconds and then starts a write that takes 1 second. Is the write safe?]
Not necessarily. The process can be paused for longer than 9 seconds between the check and the write. When it resumes, the lease has expired and may belong to another node, but the code carries on as if nothing had happened.
:::

## Knowledge, truth and lies

A node cannot know anything for certain about the rest of the system. It can only guess from the messages it receives, or fails to receive.

### The majority decides

A node cannot even trust its own judgment about itself. It may believe it is the leader while every other node, having heard nothing from it, has elected a replacement. So important decisions are not left to one node. They require agreement from a **quorum**, usually a majority. Because there can only be one majority at a time, two conflicting decisions cannot both be approved. A node that the majority has declared dead must accept that, even if it feels fine.

### Leases and fencing tokens

A lock with a timeout is called a lease. Combine a lease with a process pause and you get the failure described above: a node whose lease expired during a pause wakes up and writes anyway, clashing with the new holder. Such a node is sometimes called a zombie.

The remedy is a **fencing token**. Every time the lock service grants the lease, it also hands out a number that only ever increases. The client sends that number with every write, and the storage system remembers the highest number it has seen and rejects anything lower. The stale client's write arrives with an old token and is refused. The essential point is that the check is made by the resource being protected, not by the client, which cannot be trusted to know its own status.

### Byzantine faults

Everything so far assumes nodes are honest: slow or dead perhaps, but not lying. A node that sends false or contradictory messages has a **Byzantine fault**. Tolerating those is needed in aircraft control systems and in blockchains, where participants do not trust each other. Inside one organization's datacentre it is usually too expensive to be worthwhile, though cheap defences against accidental corruption, such as checksums and input validation, always are.

## System models and correctness

To reason about an algorithm you state what you assume. For timing: a synchronous model assumes bounded delays, an asynchronous model assumes nothing at all, and a **partially synchronous** model, the realistic one, assumes the system behaves well most of the time and occasionally does not. For nodes: they may crash and stay down, crash and come back with whatever they saved to disk, or behave arbitrarily.

An algorithm's guarantees come in two kinds. A **safety** property says nothing bad happens, such as two nodes never both holding the lock. A **liveness** property says something good eventually happens, such as every request eventually getting a response. Good algorithms keep their safety properties always, even when every assumption fails, and promise liveness only once conditions return to normal.

## Testing for the unexpected

Bugs in this territory hide in rare timings that ordinary tests never hit. Three techniques help. Formal methods describe the algorithm precisely and have a tool explore every state for violations. Fault injection deliberately breaks a running system, cutting network links and killing processes, to see whether it copes. Deterministic simulation runs the real code in a simulated world where the test controls time, the network and every failure, so that any bug found can be replayed exactly.

## What the labs show

- **Lab 1** draws two million heartbeat delays from a realistic distribution and shows the false alarm rate and detection time for five timeouts.
- **Lab 2** shows a time-of-day clock running backward, last write wins dropping newer writes, and how little can be ordered once clocks are treated as ranges.
- **Lab 3** plays out a lease expiring during a pause, with and without fencing tokens.

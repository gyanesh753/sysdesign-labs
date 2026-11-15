## Change is the normal state

Applications change constantly, and when a feature changes, the data it stores usually changes with it. The hard part is that you can never switch everything over at once.

On the server side you deploy with a rolling upgrade: a few machines at a time, so the service stays up. For a while old and new versions run side by side. On the client side you depend on users installing an update, which some will not do for months. And data written years ago is still sitting in the database.

So two kinds of compatibility are needed at the same moment:

- **Backward compatibility**: newer code can read data written by older code.
- **Forward compatibility**: older code can read data written by newer code.

Backward compatibility is the easier one, because when you write the new code you know what the old data looked like. Forward compatibility is harder: old code has to cope with things that did not exist when it was written, which in practice means ignoring them gracefully.

## Formats for encoding data

In memory, data lives in objects and structures full of pointers. To write it to a file or send it over a network it must be turned into a self-contained sequence of bytes. That translation is called **encoding** (or serialization), and the reverse is decoding.

### Language-specific formats

Most languages can dump their objects to bytes with one call. It is convenient and almost always a mistake for anything long-lived. The result ties you to one language, decoding can often be tricked into running arbitrary code, and versioning is an afterthought.

### JSON, XML and CSV

Text formats are readable and understood everywhere, which makes them a good default for exchanging data between organizations. Their weaknesses are worth knowing. Numbers are ambiguous: JSON does not separate integers from floating point, and large integers lose precision in some languages. Binary data has to be smuggled in as text. Schemas exist but are optional, so much of the structure ends up hard-coded in the applications on each side. And every record repeats every field name.

### Binary formats with field tags

For data used inside one organization, a schema-based binary format is smaller and safer. You describe each record type in a schema, and a tool generates code to encode and decode it.

In the Protocol Buffers style, the schema gives every field a number, called a **tag**. The encoded bytes contain the tag and the value, never the field name. That is what makes evolution possible, and it gives clear rules:

- You may add a field, as long as it has a new tag number and is optional or has a default. Old code skips tags it does not recognize; new code fills in the default when reading old data.
- You may rename a field freely, because names are not in the data.
- You may never change a field's tag number or reuse an old one, and you may not add a field that is required.

:::checkpoint[You add a required field to a message type and deploy the new code. What breaks?]
Reading old data. Every record written before the change lacks the field, so new code rejects it. That is a backward compatibility failure, and it is why new fields must be optional or have a default.
:::

### The writer's schema and the reader's schema

The Avro style goes further and puts no tags in the data at all. Values are simply written one after another in the order the schema lists them. That is the most compact encoding, but the bytes are meaningless unless you know the exact schema that wrote them.

So decoding uses two schemas: the **writer's schema**, which the data was written with, and the **reader's schema**, which the application expects. The library matches fields between them by name, ignores fields the reader does not want, and fills in defaults for fields the writer did not have.

How does the reader learn the writer's schema? It depends on the setting. A large file states it once at the top. A database record can carry a small version number that points into a registry of schemas. Two processes on a network connection can agree on it when they connect. Because there are no tag numbers to assign by hand, this style suits schemas that are generated automatically, for example from a database table.

### Why schemas are worth it

Beyond compactness, a schema is documentation that cannot go out of date, since decoding depends on it. A registry of schema versions lets you check compatibility before you deploy. And generated code gives type checking at compile time.

## How data flows between processes

Compatibility is a relationship between the process that encodes and the process that decodes. Who those are depends on how the data travels.

### Through a database

The writer is your application, and the reader is a later version of your application, or an older one that is still running. A database is in effect a message to your future self. Data outlives code: a row written five years ago is still in its original encoding unless something rewrote it.

There is a specific trap here. Old code reads a record written by new code, updates one field, and writes it back. If it rebuilt the record from only the fields it knows about, the new field has just been erased. Old code must carry unknown fields through untouched. Lab 2 shows the loss and the fix.

### Through services

When a client calls a server over the network, the request is encoded by one and decoded by the other, and the response goes the other way. The two common styles are REST, which builds on the features of HTTP, and remote procedure calls, which try to make a network request look like calling a function.

That resemblance is misleading, because a network call differs from a local call in ways that matter:

- A local call either returns or throws. A network call can also simply never answer, and you cannot tell whether the request was lost, the server is slow, or the reply was lost.
- If you retry after a timeout, the action may happen twice, unless the operation is **idempotent**, meaning repeating it has the same effect as doing it once.
- It takes far longer, and how long varies widely.
- Arguments must be encoded into bytes, which is awkward for large objects, and the two sides may be written in different languages.

For evolving services, it is usual to update servers first and clients later. That means you need backward compatibility on requests and forward compatibility on responses. For public APIs you cannot force clients to upgrade, so compatibility has to be kept for a very long time, often by running several API versions side by side.

### Through durable workflows

A business process made of several steps, such as charge the card, reserve the stock, send the email, is fragile when written as plain service calls: a crash in the middle leaves it half done. **Durable execution** frameworks record the result of each completed step in a log. If the process fails, it is re-run and the framework replays the recorded results up to the point of failure, so no completed step is repeated. The price is that workflow code must be deterministic, and changing it while workflows are in flight needs care.

### Through message brokers

In between sits asynchronous messaging. The sender hands a message to a broker and does not wait for the recipient. The broker buffers messages if the recipient is down or overloaded, redelivers them if it crashes, lets one message go to several recipients, and means the sender does not need to know who they are. Since a consumer may republish messages to another topic, the same rule about preserving unknown fields applies.

## What the labs show

- **Lab 1** encodes one record as JSON, with field tags, and in schema order, and prints the bytes.
- **Lab 2** plays out a rolling upgrade: new code reading old data, old code reading new data, the rewrite trap, and two breaking changes.

# lab1_few_shot.py - AIE Ch 5: the same task with a vague prompt, a clear prompt, and a clear prompt with examples
from llm import MODEL, chat

LABELS = ['billing', 'technical', 'account', 'other']
MESSAGES = [
    ('I was charged twice for my subscription this month.', 'billing'),
    ('The app crashes every time I open the settings page.', 'technical'),
    ('How do I change the email address on my profile?', 'account'),
    ('Do you have an office in Pune?', 'other'),
    ('My invoice shows the wrong tax amount.', 'billing'),
    ('I cannot log in even after resetting my password.', 'account'),
    ('Video calls keep freezing after about ten minutes.', 'technical'),
    ('Can I get a refund for the annual plan?', 'billing'),
    ('Please delete my account and all my data.', 'account'),
    ('The export button produces an empty file.', 'technical'),
    ('What are your support hours during holidays?', 'other'),
    ('I want to upgrade from the basic plan to premium.', 'billing'),
    ('Two-factor codes are not arriving on my phone.', 'account'),
    ('Search returns no results for words with accents.', 'technical'),
    ('Is there a student discount?', 'billing'),
    ('I would like to give feedback on your new logo.', 'other'),
    ('The mobile app drains my battery very quickly.', 'technical'),
    ('How do I add a second user to my team workspace?', 'account'),
    ('My card was declined but the money left my bank.', 'billing'),
    ('Are you hiring software engineers?', 'other'),
]

PROMPTS = {
    'vague': lambda m: f'What kind of support message is this?\n\n{m}',
    'clear instructions': lambda m: ('Classify the customer message into exactly one category: billing, technical, account, or other.\n'
                                     'billing = payments, invoices, refunds, plans and prices. technical = something in the product is not working. '
                                     'account = login, profile, security, users and data. other = anything else.\n'
                                     'Reply with the category word only, in lowercase.\n\n' f'Message: {m}'),
    'clear + 4 examples': lambda m: ('Classify the customer message into exactly one category: billing, technical, account, or other.\n'
                                     'billing = payments, invoices, refunds, plans and prices. technical = something in the product is not working. '
                                     'account = login, profile, security, users and data. other = anything else.\n'
                                     'Reply with the category word only, in lowercase.\n\n'
                                     'Message: I need a copy of last month\'s receipt.\nCategory: billing\n\n'
                                     'Message: The page stays blank after I click save.\nCategory: technical\n\n'
                                     'Message: How do I turn on login alerts?\nCategory: account\n\n'
                                     'Message: Where can I read your press releases?\nCategory: other\n\n'
                                     f'Message: {m}\nCategory:'),
}

print(f'model: {MODEL}, {len(MESSAGES)} messages, temperature 0\n')
print(f'{"prompt":<22}{"usable output":>15}{"correct":>10}{"avg output length":>20}')
for name, build in PROMPTS.items():
    usable = correct = chars = 0
    sample, misses = None, []
    for message, label in MESSAGES:
        out = chat(build(message), max_tokens=60)
        chars += len(out)
        cleaned = out.lower().strip(' .\n"\'')
        if cleaned in LABELS:                      # code downstream needs exactly one of the four words
            usable += 1
            correct += cleaned == label
        sample = sample or out
        if cleaned in LABELS and cleaned != label:
            misses.append(f'{message[:44]!r} -> {cleaned} (expected {label})')
    n = len(MESSAGES)
    print(f'{name:<22}{usable / n:>15.0%}{correct / n:>10.0%}{chars / n:>14.0f} chars')
    print(f'    first reply: {sample[:90]!r}')
    for miss in misses[:3]:
        print(f'    wrong: {miss}')
print('\n"Usable" means the reply is exactly one of the four labels, which is what a program reading it would need.')

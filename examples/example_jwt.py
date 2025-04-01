import sys
import random
import string
sys.path.append("/Users/waldnzwrld/Code/quotient-python")
from quotientai import QuotientAI

quotient = QuotientAI()

def generate_random_text(length=10):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

new_prompt = quotient.prompts.create(
    name=generate_random_text(length=10),
    system_prompt=generate_random_text(length=100),
    user_prompt=generate_random_text(length=100)
)

print(new_prompt)
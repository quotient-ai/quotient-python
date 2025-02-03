from quotientai import QuotientAI

quotient = QuotientAI()

# create a prompt
prompt = quotient.prompts.create(
    name="quotient-demo-prompt",
    system_prompt="I have a problem",
    user_prompt="Here is a user's inquiry {{input}}, and the context {{context}}",
)


# create a dataset
dataset = quotient.datasets.create(
    name="customer-support-augmentation-v1",
    rows=[
        {
            "input": "I have a problem",
            "context": "here is a support ticket",
            "expected": "I'm sorry to hear that. What's the problem?",
            "annotation": "good",
            "annotation_note": "this is a good example",
        },
        # expected is optional, so we should be able to create a row without it
        {
            "input": "I need help",
            "context": "here is a support ticket",
            "annotation": "good",
            "annotation_note": "this is a good example",
        },
        # context is also optional, so we should be able to create a row without it
        {
            "input": "I want to cancel my subscription",
            "expected": "I'm sorry to hear that. I can help you with that. Please provide me with your account information.",
        },
    ],
)

# list out the models
models = quotient.models.list()

# get gpt4o-mini model
model = next((model for model in models if model.name == 'gpt-4o-mini-2024-07-18'))

# create a run with all of the metrics we care about
run = quotient.evaluate(
    prompt=prompt,
    dataset=dataset,
    model=model,
    parameters={
        "temperature": 0.7,
        "top_k": 50,
        "top_p": 0.9,
        "max_tokens": 100,
    },
    metrics=[
        'bertscore',
        'exactmatch',
        'verbosity_ratio',
    ],
)

print("Run ID:", run.id)

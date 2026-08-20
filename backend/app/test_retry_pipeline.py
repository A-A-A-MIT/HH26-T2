from pipeline import run_pipeline


context_chunks = [
    {
        "text": "Paris is the capital and largest city of France.",
        "source": "doc_001",
        "score": 0.94
    }
]


class FakeGenerator:

    def __init__(self):
        self.calls = 0

    def __call__(
        self,
        question: str,
        context: str,
        retry: bool = False
    ) -> str:

        self.calls += 1

        # First attempt deliberately produces
        # an unsupported answer.
        if self.calls == 1:
            return "Paris has a population of 2 million people."

        # Retry produces a grounded answer.
        return "Paris is the capital of France."


fake_generator = FakeGenerator()


result = run_pipeline(
    question="What is the capital of France?",
    retrieved_chunks=context_chunks,
    generator=fake_generator
)


print("RESULT:")
print(result)

print("\nGENERATOR CALLS:")
print(fake_generator.calls)
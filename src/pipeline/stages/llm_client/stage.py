from pipeline.contracts.models import GenerationResult, PromptBundle


class OllamaStubClient:
    def generate(self, prompt: PromptBundle) -> GenerationResult:
        _ = prompt
        # Replace this stub with a real Ollama call in the next iteration.
        reply = "That sounds heavy. I am here with you. Do you want to share what feels most present right now?"
        return GenerationResult(raw_text=reply, metadata={"provider": "ollama-stub"})

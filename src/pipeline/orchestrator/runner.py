import uuid

from pipeline.contracts.models import RequestEnvelope
from pipeline.orchestrator.pipeline import EmotivePipeline


def main() -> None:
    pipeline = EmotivePipeline()
    request = RequestEnvelope(
        request_id=str(uuid.uuid4()),
        user_id="local-user",
        user_input="I have been feeling lonely and anxious lately.",
        trace_id=str(uuid.uuid4()),
    )
    response = pipeline.run(request)
    print("Response:")
    print(response.text)
    if response.safety_notes:
        print("Safety notes:")
        for note in response.safety_notes:
            print(f"- {note}")


if __name__ == "__main__":
    main()

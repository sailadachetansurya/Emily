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
    result = pipeline.run(request)
    print("Response:")
    print(result.response.text)
    if result.response.safety_notes:
        print("Safety notes:")
        for note in result.response.safety_notes:
            print(f"- {note}")
    print("Traces:")
    for trace in result.traces:
        print(f"- {trace.stage_name}: {trace.status}")


if __name__ == "__main__":
    main()

from pipeline.contracts.models import RequestEnvelope


class DefaultInputGateway:
    def normalize(self, request: RequestEnvelope) -> RequestEnvelope:
        normalized_text = " ".join(request.user_input.strip().split())
        return RequestEnvelope(
            request_id=request.request_id,
            user_id=request.user_id,
            user_input=normalized_text,
            trace_id=request.trace_id,
        )

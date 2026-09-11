"""A small OpenAPI document in the shape the client expects. NOT Form King's spec; it exists
so the spec reader, cost parser and client can be tested without the real file."""

MINI_SPEC = {
    "openapi": "3.0.3",
    "info": {
        "title": "Mini",
        "version": "0.0.1",
        "description": "Credit costs:\n| Operation | Credits |\n| Get Upcoming Meetings | 1 |\n| Get Meeting Speedmaps | 5 |\n",
    },
    "servers": [{"url": "https://example.test/v1/"}],
    "components": {
        "securitySchemes": {"ApiKeyAuth": {"type": "apiKey", "in": "header", "name": "X-API-Key"}},
        "parameters": {"NumBenchmarks": {"name": "numBenchmarks", "in": "query", "required": False, "schema": {"type": "integer", "default": 5}}},
    },
    "paths": {
        "/meetings/upcoming": {"get": {"summary": "Get Upcoming Meetings", "operationId": "getUpcomingMeetings"}},
        "/meetings/{meetingId}/speedmaps": {
            "parameters": [{"name": "meetingId", "in": "path", "required": True, "schema": {"type": "string"}}],
            "get": {"summary": "Get Meeting Speedmaps", "operationId": "getMeetingSpeedmaps"},
        },
        "/races/{raceId}/form": {
            "get": {
                "summary": "Get Race Form", "operationId": "getRaceForm",
                "description": "Full form for a race. Costs 30 credits per call.",
                "parameters": [
                    {"name": "raceId", "in": "path", "required": True, "schema": {"type": "string"}},
                    {"$ref": "#/components/parameters/NumBenchmarks"},
                ],
            }
        },
        "/horses/{horseId}": {
            "get": {
                "summary": "Get Horse Profile", "operationId": "getHorseProfile",
                "x-credits": [{"when": {"numBenchmarks": "<=5"}, "cost": 0}, {"cost": 4}],
                "parameters": [
                    {"name": "horseId", "in": "path", "required": True, "schema": {"type": "string"}},
                    {"$ref": "#/components/parameters/NumBenchmarks"},
                ],
            }
        },
        "/races/{raceId}/results": {
            "get": {"summary": "Get Race Results", "operationId": "getRaceResults",
                    "parameters": [{"name": "raceId", "in": "path", "required": True, "schema": {"type": "string"}}]}
        },
    },
}

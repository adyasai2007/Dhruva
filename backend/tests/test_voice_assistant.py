"""
Test Suite for DHRUVA Voice Assistant Service.
Verifies all backend tools, intent understanding, default resolution,
and integration with the 5D recommendation and itinerary engines.
"""

import pytest
from backend.database.db import db_repo
from backend.database.db_service import dhruva_db
from backend.services.voice_assistant import voice_assistant, GEMINI_VOICE_TOOLS


class TestVoiceAssistantTools:
    """Test individual tool execution."""

    def test_tool_declarations(self):
        assert len(GEMINI_VOICE_TOOLS) >= 7
        names = [t["name"] for t in GEMINI_VOICE_TOOLS]
        assert "get_city" in names
        assert "get_city_interests" in names
        assert "search_places" in names
        assert "get_place_details" in names
        assert "get_festivals" in names
        assert "create_itinerary" in names
        assert "navigate_ui" in names

    def test_get_city_tool(self):
        res = voice_assistant.execute_tool("get_city", {"city_name": "Puri"})
        assert "city" in res
        assert res["city"]["name"] == "Puri"

    def test_get_city_interests_tool(self):
        res = voice_assistant.execute_tool("get_city_interests", {"city_id": 1})
        assert "city_interest" in res
        assert "spiritual" in res["city_interest"]

    def test_search_places_with_user_preferences(self):
        res = voice_assistant.execute_tool("search_places", {
            "city_name": "Bhubaneswar",
            "preferences": {"spiritual": 5.0, "architecture": 4.8},
            "limit": 4
        })
        assert "places" in res
        assert res["ranking_mode"] == "user_preferences"
        assert len(res["places"]) > 0
        assert "match_percentage" in res["places"][0]

    def test_search_places_with_default_city_interest(self):
        res = voice_assistant.execute_tool("search_places", {
            "city_name": "Puri",
            "preferences": None,
            "limit": 4
        })
        assert "places" in res
        assert res["ranking_mode"] == "city_interest_default"

    def test_get_place_details_tool(self):
        res = voice_assistant.execute_tool("get_place_details", {"place_id": 1})
        assert "place" in res
        assert res["place"]["id"] == 1
        assert "entry_fee" in res["place"]

    def test_get_opening_hours_tool(self):
        res = voice_assistant.execute_tool("get_opening_hours", {"place_id": 1})
        assert "opening_hours" in res
        assert isinstance(res["opening_hours"], list)

    def test_get_festivals_tool(self):
        res = voice_assistant.execute_tool("get_festivals", {"city_name": "Puri"})
        assert "festivals" in res
        assert res["count"] > 0

    def test_create_itinerary_tool(self):
        res = voice_assistant.execute_tool("create_itinerary", {
            "city_name": "Puri",
            "num_days": 3,
            "start_date": "2026-10-15"
        })
        assert res["status"] == "success"
        itinerary = res["itinerary"]
        assert len(itinerary["days"]) == 3

    def test_navigate_ui_tool(self):
        res = voice_assistant.execute_tool("navigate_ui", {"screen": "explore", "target_id": "puri"})
        assert res["action"] == "navigate_ui"
        assert res["screen"] == "explore"


class TestVoiceConversationalTurns:
    """Test conversation turns."""

    def test_plan_trip_turn(self):
        res = voice_assistant.process_conversation_turn("Plan a 3-day spiritual trip to Puri")
        assert res["status"] == "success"
        assert res["itinerary"] is not None
        assert len(res["itinerary"]["days"]) == 3
        assert res["navigation"]["action"] == "view_itinerary"

    def test_missing_destination_prompts_user(self):
        res = voice_assistant.process_conversation_turn("Plan me a 2-day trip")
        assert res["status"] == "success"
        reply = res["reply"].lower()
        assert "which" in reply or "city" in reply or "bhubaneswar" in reply or "puri" in reply

    def test_specific_monument_inquiry(self):
        res = voice_assistant.process_conversation_turn("Tell me about Rajarani Temple")
        assert res["status"] == "success"
        assert "Rajarani" in res["reply"]
        assert res["navigation"]["action"] == "open_modal"


class TestGeminiLiveAPIIntegration:
    """Test Gemini API invocation, role mapping, and fallback handling."""

    def test_gemini_role_normalization_and_tool_synthesis(self, monkeypatch):
        import json
        import io

        calls = []

        class MockResponse:
            def __init__(self, data):
                self._data = data

            def read(self):
                return json.dumps(self._data).encode("utf-8")

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                pass

        def mock_urlopen(req, timeout=20):
            payload = json.loads(req.data.decode("utf-8"))
            calls.append({"url": req.full_url, "payload": payload})

            # If tool response synthesis turn
            if "role" in payload["contents"][-1] and payload["contents"][-1]["role"] == "function":
                return MockResponse({
                    "candidates": [{
                        "content": {
                            "parts": [{"text": "Puri is renowned for its sacred Jagannath Temple and pristine beaches."}],
                            "role": "model"
                        }
                    }]
                })

            # Initial Gemini turn calling get_city
            return MockResponse({
                "candidates": [{
                    "content": {
                        "parts": [{
                            "functionCall": {
                                "name": "get_city",
                                "args": {"city_name": "Puri"}
                            }
                        }],
                        "role": "model"
                    }
                }]
            })

        import urllib.request
        monkeypatch.setattr(urllib.request, "urlopen", mock_urlopen)

        history = [
            {"role": "user", "content": "Hello DHRUVA"},
            {"role": "assistant", "content": "Namaste! How may I assist you?"}
        ]

        res = voice_assistant._call_gemini_api(
            user_message="Tell me about Puri",
            history=history,
            api_key="AIzaSyTestValidKey12345",
            model_name="gemini-2.0-flash"
        )

        assert res["status"] == "success"
        assert len(calls) == 2

        # Check that history role 'assistant' was normalized to 'model'
        first_turn_contents = calls[0]["payload"]["contents"]
        roles = [c["role"] for c in first_turn_contents]
        assert "assistant" not in roles
        assert roles == ["user", "model", "user"]

        # Check tool execution & synthesis
        assert any(tc["name"] == "get_city" for tc in res["tool_calls"])
        assert "Jagannath" in res["reply"] or "Puri" in res["reply"]

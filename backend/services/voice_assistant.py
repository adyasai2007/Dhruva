"""
DHRUVA — Conversational & Navigational Voice Assistant Service.
Powered by Gemini Live API / Function Calling Architecture.

Exposes high-level backend tools to Gemini. Gemini executes no raw SQL;
the backend executes all queries, applies the 5D MIN_INTEREST recommendation logic,
runs the cultural itinerary engine, and handles UI navigation handoffs.
"""

from __future__ import annotations
import json
import logging
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, date, timezone
from typing import Dict, Any, List, Optional

from backend.config import settings
from backend.database.db import db_repo
from backend.database.db_service import dhruva_db, DhruvaDBService
from backend.algorithm.scoring import calculate_interest_similarity
from backend.services.itinerary_engine import CulturalItineraryEngine, UserPlannerPreferences

logger = logging.getLogger("dhruva.voice_assistant")

SYSTEM_INSTRUCTION = """You are DHRUVA — a culturally grounded, respectful, and intelligent voice travel guide for India.
You specialize in the living heritage, sacred sanctums, temple architecture, and cultural traditions of Odisha (Bhubaneswar, Puri, Cuttack).

CORE RESPONSIBILITIES:
1. Understand natural-language travel requests (e.g. "Plan a 3-day spiritual trip to Puri").
2. Extract destination city, duration/dates, cultural interests, and constraints.
3. If critical information (like destination city or number of days) is missing and has no sensible default, ask the user conversationally and concisely.
4. If information is omitted but has a defined application default (e.g. interest weights omitted -> use destination's CITY_INTEREST profile; pacing omitted -> use comfortable senior-friendly pacing), use that default immediately without unnecessary interrogation.
5. Never fabricate database facts, opening hours, or ticket fees. Always call backend tools. When asked about a specific temple or monument, call `get_place_details`.
6. Provide soothing, culturally rich, and concise spoken responses (2-3 sentences) suitable for voice delivery.
7. Call `navigate_ui`, `get_place_details`, or `create_itinerary` when appropriate to guide the traveler through the application screens.
"""

# Gemini Function Tool Declarations
GEMINI_VOICE_TOOLS = [
    {
        "name": "get_city",
        "description": "Retrieve detailed metadata and default 5D cultural interest profile (CITY_INTEREST) for a destination city.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "city_name": {
                    "type": "STRING",
                    "description": "Name of the city (e.g., 'Bhubaneswar', 'Puri', 'Cuttack')"
                },
                "city_id": {
                    "type": "INTEGER",
                    "description": "Optional city ID (1 for Bhubaneswar, 2 for Puri, 3 for Cuttack)"
                }
            }
        }
    },
    {
        "name": "get_city_interests",
        "description": "Retrieve the default 5D cultural baseline vector (CITY_INTEREST) for a destination city.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "city_id": {
                    "type": "INTEGER",
                    "description": "City ID (1: Bhubaneswar, 2: Puri, 3: Cuttack)"
                }
            },
            "required": ["city_id"]
        }
    },
    {
        "name": "search_places",
        "description": "Search and rank cultural heritage attractions in a city using the 5D MIN_INTEREST cosine ranking engine.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "city_id": {"type": "INTEGER", "description": "City ID (1: Bhubaneswar, 2: Puri, 3: Cuttack)"},
                "city_name": {"type": "STRING", "description": "City name"},
                "category": {"type": "STRING", "description": "Category filter (e.g., 'Temple & Sacred Sanctum', 'Heritage & Archaeological Site', 'Arts, Crafts & Museum')"},
                "preferences": {
                    "type": "OBJECT",
                    "description": "Optional 5D user interest weights (spiritual, architecture, history, nature, culture). If omitted, city CITY_INTEREST is used automatically.",
                    "properties": {
                        "spiritual": {"type": "NUMBER"},
                        "architecture": {"type": "NUMBER"},
                        "history": {"type": "NUMBER"},
                        "nature": {"type": "NUMBER"},
                        "culture": {"type": "NUMBER"}
                    }
                },
                "limit": {"type": "INTEGER", "description": "Maximum number of places to return (default 6)"}
            }
        }
    },
    {
        "name": "get_place_details",
        "description": "Retrieve verified factual details for a place including entry fee, opening hours, cultural etiquette, and 5D interest dimensions.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "place_id": {"type": "INTEGER", "description": "Optional unique ID of the cultural place"},
                "place_name": {"type": "STRING", "description": "Optional name of the cultural place (e.g. 'Rajarani Temple', 'Lingaraja Temple', 'Jagannath Temple')"}
            }
        }
    },
    {
        "name": "get_opening_hours",
        "description": "Retrieve the full weekly schedule, darshan timings, and midday sanctum rest hours for a place.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "place_id": {"type": "INTEGER", "description": "Optional place ID"},
                "place_name": {"type": "STRING", "description": "Optional place name"}
            }
        }
    },
    {
        "name": "get_festivals",
        "description": "Retrieve regional cultural festivals and celebration dates (e.g., Rath Yatra, Maha Shivaratri, Bali Yatra).",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "city_id": {"type": "INTEGER", "description": "Optional city ID"},
                "city_name": {"type": "STRING", "description": "Optional city name"}
            }
        }
    },
    {
        "name": "create_itinerary",
        "description": "Generate an algorithmic multi-day cultural itinerary with fatigue pacing, transit buffers, and sanctum schedule verification.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "city_name": {"type": "STRING", "description": "Destination city (Bhubaneswar, Puri, Cuttack)"},
                "num_days": {"type": "INTEGER", "description": "Number of days (e.g. 1, 2, 3, 4)"},
                "start_date": {"type": "STRING", "description": "Start date in YYYY-MM-DD format"},
                "pacing": {"type": "STRING", "description": "Pacing profile: 'relaxed', 'balanced', or 'intensive' (default 'relaxed')"},
                "age": {"type": "INTEGER", "description": "Traveler age (default 55 for mindful senior pacing)"},
                "interests": {
                    "type": "OBJECT",
                    "description": "5D interest weights (spiritual, architecture, history, nature, culture)",
                    "properties": {
                        "spiritual": {"type": "NUMBER"},
                        "architecture": {"type": "NUMBER"},
                        "history": {"type": "NUMBER"},
                        "nature": {"type": "NUMBER"},
                        "culture": {"type": "NUMBER"}
                    }
                },
                "mandatory_place_ids": {
                    "type": "ARRAY",
                    "items": {"type": "INTEGER"},
                    "description": "Place IDs that must be included in the itinerary"
                }
            },
            "required": ["city_name", "num_days"]
        }
    },
    {
        "name": "navigate_ui",
        "description": "Direct the frontend application to display a screen, place detail modal, or itinerary.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "screen": {
                    "type": "STRING",
                    "description": "Target screen: 'explore', 'trip_planner', 'itinerary', 'place_details', 'home', 'profile'"
                },
                "target_id": {
                    "type": "STRING",
                    "description": "Optional target place ID or destination ID (e.g. '1', 'puri')"
                },
                "query_params": {
                    "type": "OBJECT",
                    "description": "Optional URL query parameters"
                }
            },
            "required": ["screen"]
        }
    }
]

VOICE_TOOL_DECLARATIONS = GEMINI_VOICE_TOOLS


class VoiceAssistantService:
    """Core Voice Assistant service implementing Gemini Live tool orchestration and fallback NLP."""

    def __init__(self, db_service: Optional[DhruvaDBService] = None):
        self.db = db_service or dhruva_db
        self.itinerary_engine = CulturalItineraryEngine(self.db)

    def execute_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute backend tool against the local PostgreSQL service and recommendation engine."""
        logger.info(f"Executing Voice Assistant Tool: {tool_name} with args {args}")

        try:
            if tool_name == "get_city":
                c_name = args.get("city_name")
                c_id = args.get("city_id")
                if c_id:
                    city = self.db.get_city_by_id(c_id)
                elif c_name:
                    city = self.db.get_city_by_name(c_name)
                else:
                    city = self.db.get_city_by_id(1)
                return {"city": city} if city else {"error": "City not found"}

            elif tool_name == "get_city_interests":
                cid = int(args.get("city_id", 1))
                c_int = self.db.get_city_interest(cid)
                return {"city_id": cid, "city_interest": c_int}

            elif tool_name == "search_places":
                c_name = args.get("city_name")
                c_id = args.get("city_id")
                category = args.get("category")
                prefs = args.get("preferences")
                limit = args.get("limit", 6)

                places = self.db.get_places(
                    city_id=c_id,
                    city_name=c_name,
                    category=category,
                    user_interests=prefs,
                    limit=limit
                )
                return {
                    "count": len(places),
                    "ranking_mode": "user_preferences" if prefs else "city_interest_default",
                    "places": places
                }

            elif tool_name == "get_place_details":
                pid = args.get("place_id")
                pname = args.get("place_name")
                place = None
                if pid is not None:
                    place = self.db.get_place_by_id(int(pid))
                elif pname:
                    all_places = self.db.get_places(limit=100)
                    pname_lower = pname.lower().strip()
                    for p in all_places:
                        if pname_lower in p["name"].lower() or p["name"].lower() in pname_lower:
                            place = p
                            break
                if not place and pid is None and not pname:
                    place = self.db.get_place_by_id(1)
                return {"place": place} if place else {"error": f"Place '{pname or pid}' not found"}

            elif tool_name == "get_opening_hours":
                pid = args.get("place_id")
                pname = args.get("place_name")
                place = None
                if pid is not None:
                    place = self.db.get_place_by_id(int(pid))
                elif pname:
                    all_places = self.db.get_places(limit=100)
                    pname_lower = pname.lower().strip()
                    for p in all_places:
                        if pname_lower in p["name"].lower() or p["name"].lower() in pname_lower:
                            place = p
                            break
                if place:
                    return {"place_id": place["id"], "name": place["name"], "opening_hours": place.get("opening_hours", [])}
                return {"error": f"Place '{pname or pid}' not found"}

            elif tool_name == "get_festivals":
                c_name = args.get("city_name")
                c_id = args.get("city_id")
                festivals = self.db.get_festivals(city_id=c_id, city_name=c_name)
                return {"count": len(festivals), "festivals": festivals}

            elif tool_name == "create_itinerary":
                c_name = args.get("city_name", "Bhubaneswar")
                num_days = int(args.get("num_days", 2))
                start_date = args.get("start_date") or date.today().isoformat()
                pacing = args.get("pacing", "relaxed")
                age = int(args.get("age", 55))
                interests = args.get("interests")
                mandatory_ids = args.get("mandatory_place_ids", [])

                # Sensible default: use CITY_INTEREST if no interests provided
                if not interests:
                    city_obj = self.db.get_city_by_name(c_name)
                    if city_obj and city_obj.get("city_interest"):
                        interests = city_obj["city_interest"]
                    else:
                        interests = {"spiritual": 4.5, "architecture": 4.5, "history": 4.0, "nature": 2.5, "culture": 4.5}

                planner_prefs = UserPlannerPreferences(
                    city_name=c_name,
                    start_date=start_date,
                    num_days=num_days,
                    age=age,
                    pacing=pacing,
                    interests=interests,
                    mandatory_place_ids=mandatory_ids
                )
                plan = self.itinerary_engine.generate_itinerary(planner_prefs)
                return {"status": "success", "itinerary": plan}

            elif tool_name == "navigate_ui":
                screen = args.get("screen", "explore")
                target_id = args.get("target_id")
                query_params = args.get("query_params", {})
                return {
                    "action": "navigate_ui",
                    "screen": screen,
                    "target_id": target_id,
                    "query_params": query_params,
                    "status": "success"
                }

            else:
                return {"error": f"Unknown tool: {tool_name}"}

        except Exception as e:
            logger.error(f"Tool execution failed: {tool_name}: {e}", exc_info=True)
            return {"error": str(e)}

    def process_conversation_turn(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Process user speech/text turn through Gemini function-calling or fallback engine."""
        history = list(conversation_history or [])
        api_key = os.getenv("GEMINI_API_KEY", "").strip().strip('"').strip("'")
        model_env = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite").strip().strip('"').strip("'")

        is_placeholder = (
            not api_key
            or api_key.startswith("your_")
            or api_key.endswith("_Akey_here")
            or api_key.endswith("_here")
            or "your_gemini_api_key" in api_key.lower()
        )

        # If a valid Gemini API key is present, execute via Gemini Live REST API
        if not is_placeholder:
            try:
                gemini_res = self._call_gemini_api(user_message, history, api_key, model_env)
                return gemini_res
            except Exception as e:
                logger.warning(f"Gemini API request failed: {e}. Using deterministic local voice engine.")

        # Local NLP Engine Fallback
        return self._local_conversational_fallback(user_message, history, context)

    def _call_gemini_api(
        self,
        user_message: str,
        history: List[Dict[str, Any]],
        api_key: str,
        model_name: str = "gemini-3.1-flash-lite"
    ) -> Dict[str, Any]:
        """Communicate with Google Gemini API with function calling loop."""
        contents = []
        for turn in history:
            raw_role = turn.get("role", "user")
            # Google Gemini API strictly requires role to be 'user' or 'model'
            role = "model" if raw_role in ("assistant", "model") else "user"
            parts = turn.get("parts")
            if not parts:
                content_text = turn.get("content", "")
                parts = [{"text": content_text if content_text else "..."}]
            contents.append({"role": role, "parts": parts})

        contents.append({"role": "user", "parts": [{"text": user_message}]})

        payload = {
            "contents": contents,
            "systemInstruction": {"parts": [{"text": SYSTEM_INSTRUCTION}]},
            "tools": [{"functionDeclarations": GEMINI_VOICE_TOOLS}],
            "generationConfig": {"temperature": 0.2, "maxOutputTokens": 800}
        }

        candidate_models = [model_name, "gemini-3.1-flash-lite", "gemini-3.5-flash", "gemini-3.5-flash-lite", "gemini-3-flash-preview", "gemini-flash-latest"]
        unique_models = list(dict.fromkeys(candidate_models))

        res_data = None
        last_err = None
        active_model = model_name

        for test_model in unique_models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{test_model}:generateContent?key={api_key}"
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            try:
                with urllib.request.urlopen(req, timeout=20) as response:
                    res_data = json.loads(response.read().decode("utf-8"))
                    active_model = test_model
                    break
            except urllib.error.HTTPError as he:
                err_body = ""
                try:
                    err_body = he.read().decode("utf-8", errors="ignore")
                except Exception:
                    pass
                last_err = f"HTTP {he.code} on {test_model}: {err_body or he.reason}"
                logger.debug(f"Gemini model candidate {test_model} returned error: {last_err}")
                continue
            except Exception as e:
                last_err = f"{test_model}: {str(e)}"
                logger.debug(f"Gemini model candidate {test_model} request failed: {last_err}")
                continue

        if not res_data:
            raise Exception(f"All Gemini models failed. Last error: {last_err}")

        candidates = res_data.get("candidates", [])
        if not candidates:
            return {
                "status": "success",
                "reply": "I am here to guide your cultural journey across Odisha. How may I assist you today?",
                "tool_calls": [],
                "navigation": None
            }

        first_cand = candidates[0]
        content_parts = first_cand.get("content", {}).get("parts", [])

        tool_calls = []
        navigation_action = None
        generated_itinerary = None
        text_replies = []

        for part in content_parts:
            if "functionCall" in part:
                fn = part["functionCall"]
                fn_name = fn.get("name")
                fn_args = fn.get("args", {})

                output = self.execute_tool(fn_name, fn_args)
                tool_calls.append({"name": fn_name, "args": fn_args, "result": output})

                if fn_name == "create_itinerary" and "itinerary" in output:
                    generated_itinerary = output["itinerary"]
                    navigation_action = {
                        "action": "view_itinerary",
                        "screen": "itinerary",
                        "trip_data": generated_itinerary
                    }
                elif fn_name == "navigate_ui":
                    navigation_action = output
                elif fn_name == "get_place_details" and "place" in output:
                    navigation_action = {
                        "action": "open_modal",
                        "screen": "place_details",
                        "place": output["place"]
                    }

            if "text" in part:
                text_replies.append(part["text"])

        # Tool response follow-up turn
        if tool_calls:
            try:
                second_reply = self._send_tool_response(contents, content_parts, tool_calls, api_key, active_model)
                if second_reply:
                    text_replies = [second_reply]
            except Exception as e:
                logger.warning(f"Gemini tool follow-up turn error: {e}")

        final_reply = " ".join(text_replies).strip()
        if not final_reply and tool_calls:
            first_t = tool_calls[0]
            if first_t["name"] == "create_itinerary":
                final_reply = f"I have crafted a mindful multi-day itinerary for {first_t['args'].get('city_name', 'Odisha')}. Displaying your day-by-day journey."
            elif first_t["name"] == "search_places":
                places = first_t["result"].get("places", [])
                final_reply = f"Here are {len(places)} top-ranked cultural landmarks matching your interests."
            else:
                final_reply = "I have retrieved the cultural details for you."

        # If navigation action is not set yet, check if a specific monument in the database was queried
        if not navigation_action:
            user_msg_lower = user_message.lower()
            all_places = self.db.get_places(limit=100)
            for p in all_places:
                p_name_lower = p["name"].lower()
                # Check for direct monument mentions
                if p_name_lower in user_msg_lower or (len(p_name_lower.split()) > 1 and all(w in user_msg_lower for w in p_name_lower.split()[:2])):
                    navigation_action = {
                        "action": "open_modal",
                        "screen": "place_details",
                        "place": p
                    }
                    break

        return {
            "status": "success",
            "reply": final_reply or "How can I guide your journey today?",
            "tool_calls": tool_calls,
            "navigation": navigation_action,
            "itinerary": generated_itinerary
        }

    def _send_tool_response(
        self,
        contents: List[Dict[str, Any]],
        model_parts: List[Dict[str, Any]],
        tool_calls: List[Dict[str, Any]],
        api_key: str,
        model_name: str = "gemini-3.1-flash-lite"
    ) -> Optional[str]:
        """Send function responses back to Gemini for conversational synthesis."""
        candidate_models = [model_name, "gemini-3.1-flash-lite", "gemini-3.5-flash", "gemini-3.5-flash-lite", "gemini-3-flash-preview", "gemini-flash-latest"]
        unique_models = list(dict.fromkeys(candidate_models))

        contents_copy = list(contents)
        contents_copy.append({"role": "model", "parts": model_parts})

        func_response_parts = []
        for tc in tool_calls:
            res_obj = tc["result"]
            if not isinstance(res_obj, dict):
                res_obj = {"result": res_obj}
            func_response_parts.append({
                "functionResponse": {
                    "name": tc["name"],
                    "response": res_obj
                }
            })

        contents_copy.append({"role": "function", "parts": func_response_parts})

        payload = {
            "contents": contents_copy,
            "systemInstruction": {"parts": [{"text": SYSTEM_INSTRUCTION}]},
            "generationConfig": {"temperature": 0.2, "maxOutputTokens": 600}
        }

        for test_model in unique_models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{test_model}:generateContent?key={api_key}"
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            try:
                with urllib.request.urlopen(req, timeout=20) as res:
                    data = json.loads(res.read().decode("utf-8"))
                    cands = data.get("candidates", [])
                    if cands:
                        parts = cands[0].get("content", {}).get("parts", [])
                        text_chunks = [p.get("text", "") for p in parts if "text" in p]
                        return " ".join(text_chunks).strip()
                    return None
            except Exception as e:
                logger.debug(f"Gemini tool follow-up synthesis candidate {test_model} failed: {e}")
                continue
        return None

    def _local_conversational_fallback(
        self,
        message: str,
        history: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Robust domain NLP intent parsing and tool invocation."""
        msg_low = message.lower()
        tool_calls = []
        navigation_action = None
        generated_itinerary = None

        # 1. Identify Destination City
        city_name = None
        city_id = None
        if "puri" in msg_low or "jagannath" in msg_low:
            city_name, city_id = "Puri", 2
        elif "cuttack" in msg_low or "barabati" in msg_low:
            city_name, city_id = "Cuttack", 3
        elif "bhubaneswar" in msg_low or "lingaraj" in msg_low or "temple city" in msg_low:
            city_name, city_id = "Bhubaneswar", 1

        # Check history for context retention
        if not city_name and history:
            for h in reversed(history):
                prev = str(h.get("content") or "").lower()
                if "puri" in prev:
                    city_name, city_id = "Puri", 2
                    break
                elif "cuttack" in prev:
                    city_name, city_id = "Cuttack", 3
                    break
                elif "bhubaneswar" in prev:
                    city_name, city_id = "Bhubaneswar", 1
                    break

        # 2. Extract Duration (Days)
        num_days = 2
        day_match = re.search(r"(\d+)\s*[-]?\s*(day|days|diwas)", msg_low)
        if day_match:
            num_days = int(day_match.group(1))
        elif "three" in msg_low or "3" in msg_low:
            num_days = 3
        elif "one" in msg_low or "single day" in msg_low:
            num_days = 1
        elif "two" in msg_low or "weekend" in msg_low:
            num_days = 2
        elif "four" in msg_low:
            num_days = 4

        # 3. Extract Cultural Interests
        interests = {}
        if any(w in msg_low for w in ["spiritual", "temple", "darshan", "puja", "shiva"]):
            interests["spiritual"] = 5.0
        if any(w in msg_low for w in ["architecture", "carving", "sculpture", "torana"]):
            interests["architecture"] = 5.0
        if any(w in msg_low for w in ["history", "ancient", "heritage", "kalinga"]):
            interests["history"] = 5.0
        if any(w in msg_low for w in ["craft", "pattachitra", "artisan", "handloom"]):
            interests["culture"] = 5.0
        if any(w in msg_low for w in ["nature", "lake", "lagoon", "bird", "coastal"]):
            interests["nature"] = 4.5

        # 4. Intent Dispatch:
        # A. Specific Place Detail Inquiry
        all_places = self.db.repo.get_all_places()
        sorted_places = sorted(all_places, key=lambda p: len(p.name), reverse=True)
        stopwords = {"temple", "in", "the", "of", "and", "caves", "sanctuary", "village", "odisha", "bhubaneswar", "puri", "cuttack"}

        if any(w in msg_low for w in ["tell me about", "what is", "about", "details", "entry fee", "timing", "hours"]):
            for place in sorted_places:
                p_name_low = place.name.lower()
                clean_tokens = [w for w in re.findall(r"\w+", p_name_low) if w not in stopwords and len(w) > 3]
                if p_name_low in msg_low or (clean_tokens and any(t in msg_low for t in clean_tokens)):
                    tool_output = self.execute_tool("get_place_details", {"place_id": place.id})
                    tool_calls.append({"name": "get_place_details", "args": {"place_id": place.id}, "result": tool_output})
                    p = tool_output.get("place", {})
                    fee_info = p.get("entry_fee", "Free entry")
                    return {
                        "status": "success",
                        "reply": f"{p.get('name')} is a {p.get('category')} in {city_name or 'Odisha'}. {p.get('description', '')[:140]} Entry fee: {fee_info}.",
                        "tool_calls": tool_calls,
                        "navigation": {
                            "action": "open_modal",
                            "screen": "place_details",
                            "place": p
                        }
                    }

        # B. Trip Itinerary Planning
        if any(w in msg_low for w in ["plan", "itinerary", "trip", "schedule", "journey", "tour", "day", "days"]):
            if not city_name:
                return {
                    "status": "success",
                    "reply": "I would be delighted to guide your journey. Which sacred city in Odisha are you traveling to — Bhubaneswar, Puri, or Cuttack?",
                    "tool_calls": [],
                    "navigation": None
                }

            tool_args = {
                "city_name": city_name,
                "num_days": num_days,
                "interests": interests if interests else None,
                "pacing": "relaxed",
                "age": 55
            }
            tool_output = self.execute_tool("create_itinerary", tool_args)
            tool_calls.append({"name": "create_itinerary", "args": tool_args, "result": tool_output})

            if "itinerary" in tool_output:
                generated_itinerary = tool_output["itinerary"]
                navigation_action = {
                    "action": "view_itinerary",
                    "screen": "itinerary",
                    "trip_data": generated_itinerary
                }
                reply = f"I have crafted a mindful {num_days}-day cultural itinerary in {city_name} honoring your interests. Displaying your day-by-day spiritual journey."
            else:
                reply = f"I encountered an issue generating your itinerary for {city_name}. Please let me know your preferred dates."

            return {
                "status": "success",
                "reply": reply,
                "tool_calls": tool_calls,
                "navigation": navigation_action,
                "itinerary": generated_itinerary
            }

        # C. Place Exploration
        if any(w in msg_low for w in ["explore", "places", "see", "visit", "monuments", "attractions", "recommend", "show me"]):
            target_city = city_name or "Bhubaneswar"
            tool_args = {"city_name": target_city, "preferences": interests if interests else None, "limit": 6}
            tool_output = self.execute_tool("search_places", tool_args)
            tool_calls.append({"name": "search_places", "args": tool_args, "result": tool_output})
            places = tool_output.get("places", [])
            place_names = ", ".join([p["name"] for p in places[:3]])
            return {
                "status": "success",
                "reply": f"Here are the top-ranked cultural landmarks in {target_city}, led by {place_names}. Navigating to the directory.",
                "tool_calls": tool_calls,
                "navigation": {
                    "action": "navigate_ui",
                    "screen": "explore",
                    "query_params": {"dest": target_city.lower()}
                }
            }

        # D. Festivals Inquiry
        if any(w in msg_low for w in ["festival", "rath yatra", "shivaratri", "bali yatra", "event", "celebration"]):
            target_city = city_name or "Puri"
            tool_output = self.execute_tool("get_festivals", {"city_name": target_city})
            tool_calls.append({"name": "get_festivals", "args": {"city_name": target_city}, "result": tool_output})
            fests = tool_output.get("festivals", [])
            fest_names = ", ".join([f["name"] for f in fests[:2]]) if fests else "Rath Yatra and Maha Shivaratri"
            return {
                "status": "success",
                "reply": f"Key cultural celebrations include {fest_names}. Would you like to align your journey with these dates?",
                "tool_calls": tool_calls,
                "navigation": None
            }

        # Default Greeting
        return {
            "status": "success",
            "reply": "Namaste. I am DHRUVA, your cultural travel guide. I can craft personalized itineraries for Bhubaneswar, Puri, and Cuttack, explore sacred sanctums, or check festival timings. How may I assist you?",
            "tool_calls": [],
            "navigation": None
        }


voice_assistant = VoiceAssistantService()

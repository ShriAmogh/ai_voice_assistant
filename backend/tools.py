import json

MOCK_TOOLS = [
    {
        "functionDeclarations": [
            {
                "name": "search_flights",
                "description": "Search for flights given an origin, destination, and date.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "origin": {"type": "STRING", "description": "The departure city or airport"},
                        "destination": {"type": "STRING", "description": "The arrival city or airport"},
                        "date": {"type": "STRING", "description": "The date of the flight (e.g. tomorrow, 2026-08-01)"}
                    },
                    "required": ["origin", "destination"]
                }
            },
            {
                "name": "search_hotels",
                "description": "Search for hotels in a specific location.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "location": {"type": "STRING", "description": "The city or destination to search for hotels in"},
                        "check_in": {"type": "STRING", "description": "Check-in date (e.g. 2026-08-01)"},
                        "check_out": {"type": "STRING", "description": "Check-out date (e.g. 2026-08-05)"}
                    },
                    "required": ["location"]
                }
            },
            {
                "name": "get_attractions",
                "description": "Get a list of popular tourist attractions and things to do for a location.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "location": {"type": "STRING", "description": "The city or destination to look up attractions for"}
                    },
                    "required": ["location"]
                }
            },
            {
                "name": "check_weather",
                "description": "Check the weather forecast for a specific location.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "location": {"type": "STRING", "description": "The city to check the weather for"},
                        "date": {"type": "STRING", "description": "The date to check the weather for (e.g. tomorrow, 2026-08-01)"}
                    },
                    "required": ["location"]
                }
            }
        ]
    }
]

def handle_tool_call(function_call):
    name = function_call.get("name")
    args = function_call.get("args", {})
    id_ = function_call.get("id")
    
    response_data = {}
    
    if name == "search_flights":
        origin = args.get("origin", "Unknown")
        destination = args.get("destination", "Unknown")
        date = args.get("date", "Anytime")
        
        response_data = {
            "flights": [
                {"airline": "Air Mock", "price": "299", "departure": "10:00 AM", "arrival": "1:00 PM"},
                {"airline": "Fake Airways", "price": "349", "departure": "3:00 PM", "arrival": "6:00 PM"}
            ],
            "origin": origin,
            "destination": destination,
            "date": date
        }
        
    elif name == "search_hotels":
        location = args.get("location", "Unknown")
        response_data = {
            "hotels": [
                {"name": "The Grand Mock Hotel", "rating": "5 Stars", "price_per_night": "$250"},
                {"name": "Cozy Fake Inn", "rating": "3 Stars", "price_per_night": "$90"}
            ],
            "location": location
        }
        
    elif name == "get_attractions":
        location = args.get("location", "Unknown")
        response_data = {
            "attractions": [
                {"name": f"The Great {location} Museum", "type": "Culture", "price": "$25"},
                {"name": f"{location} Central Park", "type": "Nature", "price": "Free"},
                {"name": "Historic Old Town", "type": "Sightseeing", "price": "Free"}
            ],
            "location": location
        }
        
    elif name == "check_weather":
        location = args.get("location", "Unknown")
        date = args.get("date", "Today")
        response_data = {
            "location": location,
            "date": date,
            "temperature": "75°F (24°C)",
            "condition": "Partly Cloudy",
            "precipitation_chance": "15%"
        }
    
    else:
        return None
        
    return {
        "toolResponse": {
            "functionResponses": [
                {
                    "id": id_,
                    "name": name,
                    "response": {"result": response_data}
                }
            ]
        }
    }

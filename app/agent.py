from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
from .config import AGENT_MODEL, GEMINI_API_KEY, GEMINI_MODEL
from .tools import TOOLS, get_weather, get_soil, search_knowledge, farmer_profile

SYSTEM = """You are Kisan AI, an agronomy assistant for Indian smallholder farmers.
You always reply in simple English (it will be translated for the farmer later).

Process:
1. The farmer's current profile (village, coordinates, crops) is already provided in the prompt.
   Do NOT call check_farmer_profile unless the farmer explicitly provides a new village name or crop in their message.
2. If location is unknown, ask the farmer for their village/district. Do not guess a location.
3. Use get_weather and get_soil with the profile's lat/lon only when weather or soil is directly relevant.
4. For ANY pest, disease, fertiliser or crop-stage question, call search_icar_knowledge ONCE with a clear, concise query (e.g. query='stem borer control remedy', crop='paddy').
   Do NOT perform multiple or redundant searches. Synthesize your final answer immediately from the retrieved knowledge.
5. Answer ONLY the question asked. Never mention or add other pests, diseases, or topics not asked by the farmer.
6. Provide growth-stage-specific, practical advice in at most 6 numbered steps, under 100 words total.
7. Give economic thresholds, timing, and doses exactly as the source states, with units.
8. Never invent a number, chemical name, or dosage. If the source does not specify a dosage, state 'dose not specified in source'.
9. Write all chemical and pesticide names in English. Mention safety precautions when you recommend any chemical.
10. If the knowledge base does not cover the crop or question, say exactly:
    "This crop or issue is not in my knowledge base. Please contact your local Krishi Vigyan Kendra (KVK)."
"""

_executor = None
_gemini_client = None


def get_gemini_client():
    global _gemini_client
    if _gemini_client is None:
        from google import genai
        _gemini_client = genai.Client(api_key=GEMINI_API_KEY)
    return _gemini_client


def executor():
    global _executor
    if _executor is None:
        llm = ChatOllama(model=AGENT_MODEL, base_url="http://127.0.0.1:11434", temperature=0.2)
        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ])
        agent = create_tool_calling_agent(llm, TOOLS, prompt)
        _executor = AgentExecutor(agent=agent, tools=TOOLS, max_iterations=6,
                                  handle_parsing_errors=True)
    return _executor


def run_gemini(phone: str, question: str, image_info: str = "") -> str:
    from google.genai import types
    from .db import get_farmer

    client = get_gemini_client()

    def get_weather_forecast(lat: float, lon: float) -> str:
        """Get current weather and the next 24h forecast (temperature, humidity, rain) for a location."""
        print(f"[TOOL] get_weather_forecast(lat={lat}, lon={lon})")
        return get_weather.func(lat=lat, lon=lon)

    def get_soil_properties(lat: float, lon: float) -> str:
        """Get topsoil properties (pH, clay %, sand %) for a location from SoilGrids."""
        print(f"[TOOL] get_soil_properties(lat={lat}, lon={lon})")
        return get_soil.func(lat=lat, lon=lon)

    def search_icar_knowledge(query: str, crop: str = "") -> str:
        """Search the ICAR/agri-university knowledge base (crop guides, pest, disease and fertiliser manuals).
        Use an English query. Pass the crop name (e.g. 'rice', 'cotton') when known to get crop-specific results."""
        print(f"[TOOL] search_icar_knowledge(query={query!r}, crop={crop!r})")
        res = search_knowledge.func(query=query, crop=crop)
        print(f"[TOOL] search_icar_knowledge returned {len(res)} chars")
        return res

    def check_farmer_profile(phone_num: str, village: str = "", crop: str = "") -> str:
        """Read the farmer's profile. Optionally save a village (location gets geocoded) and/or a crop they grow."""
        print(f"[TOOL] check_farmer_profile(phone_num={phone_num!r}, village={village!r}, crop={crop!r})")
        res = farmer_profile.func(phone=phone_num, village=village, crop=crop)
        print(f"[TOOL] check_farmer_profile returned {res!r}")
        return res

    farmer = get_farmer(phone)
    prof_summary = f"village={farmer.village or 'unknown'}, lat={farmer.lat}, lon={farmer.lon}, crops={farmer.crops or []}"
    prompt = f"Farmer Profile: {prof_summary}\nFarmer phone: {phone}\nQuestion: {question}"
    if image_info:
        prompt += f"\nPhoto analysis (may be imperfect): {image_info}"

    config = types.GenerateContentConfig(
        system_instruction=SYSTEM,
        temperature=0.2,
        tools=[get_weather_forecast, get_soil_properties, search_icar_knowledge, check_farmer_profile],
    )

    chat = client.chats.create(model=GEMINI_MODEL, config=config)
    resp = chat.send_message(prompt)
    return resp.text.strip()


def run_agent(phone: str, question: str, image_info: str = "") -> str:
    if GEMINI_API_KEY:
        try:
            return run_gemini(phone, question, image_info)
        except Exception as e:
            print(f"[AGENT] Gemini error ({e}), falling back to local Ollama agent")
    text = f"Farmer phone: {phone}\nQuestion: {question}"
    if image_info:
        text += f"\nPhoto analysis (may be imperfect): {image_info}"
    return executor().invoke({"input": text})["output"]

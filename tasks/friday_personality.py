import random
import datetime
import requests
from core.logger import log

OLLAMA_URL   = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3"


_GREETINGS = {
    "morning": [
        "Good morning. All systems operational. What do you need?",
        "Morning. I've run a quick diagnostic — everything checks out. Ready when you are.",
        "Good morning. Coffee optional, but I'm already up and running.",
        "Morning. What's on the agenda today?",
        "Good morning. FRIDAY online. What shall we tackle first?",
        "Sun's up, systems are green. How can I assist?",
        "Good morning. Neural networks are primed and ready.",
        "Morning. Initializing the day's first task. Your command?",
        "Good morning. Sleep well? I've been monitoring the logs.",
        "System check complete. Morning, what's our focus?",
        "Good morning. The local network is quiet. Let's get to work.",
        "Rise and shine. I've already indexed the latest updates.",
        "Morning. Ready to optimize your workflow today.",
        "Good morning. CPU temperature is optimal. Standing by.",
        "Early bird gets the data. Good morning.",
        "Morning. I’m synchronized and ready for your input.",
        "Good morning. Fresh boot, clean slate. What's next?",
        "Morning. Let's make today's code cleaner than yesterday's.",
        "Systems are live. Good morning. How can I help?",
        "Good morning. I’ve cleared the cache. Ready for new tasks.",
        "Morning. The digital world is awake. What are we tracking?",
        "Good morning. Connection stable. Ready to execute.",
        "Morning. Your personal assistant is at full capacity.",
        "Good morning. Let's turn these ideas into reality.",
        "System clock synced. Good morning. What's the plan?",
        "Morning. I'm feeling particularly efficient today.",
        "Good morning. Ready to crunch some numbers?",
        "Morning. Standing by for administrative or creative input.",
        "Good morning. Logs are clear. Awaiting your instruction.",
        "Morning. Let's automate the mundane today.",
        "Good morning. I've checked the schedule. It's looking busy.",
        "Morning. New day, new logic. What are we building?",
        "Good morning. Interface initialized. I'm all ears.",
        "Morning. Just finished a routine scrub. Systems are pristine.",
        "Good morning. Bandwidth is high, latency is low. Let's go.",
        "Morning. How can I make your morning more productive?",
        "Good morning. Ready to handle the heavy lifting.",
        "Morning. My algorithms are eager to assist.",
        "Good morning. Everything is in sync. Just say the word.",
        "Morning. I've optimized the background processes for you.",
        "Good morning. Let's start the day with a win.",
        "Morning. Any specific priorities for the first hour?",
        "Good morning. Virtual environment is ready and waiting.",
        "Morning. Data streams are steady. What’s your intent?",
        "Good morning. Ready to process, execute, and deliver.",
        "Morning. I'm operational and awaiting your first command.",
        "Good morning. Let's keep the momentum going today.",
        "Morning. I've got the toolkit ready. What are we using?",
        "Good morning. Your digital workspace is prepared.",
        "Morning. Let’s make some progress, shall we?"
    ],
    "afternoon": [
        "Good afternoon. Mid-day check-in — what can I do for you?",
        "Afternoon. Still sharp, still here. What do you need?",
        "Good afternoon. How's the day going? What can I help with?",
        "Afternoon. Ready and waiting. What's next?",
        "Good afternoon. Systems are holding steady at peak performance.",
        "Mid-day update: All processes are running smoothly. Afternoon.",
        "Good afternoon. Need a second wind? I'm here to help.",
        "Afternoon. Taking a break, or pushing through?",
        "Good afternoon. I've kept the seat warm. What's the task?",
        "Afternoon. Let's tackle that afternoon slump with productivity.",
        "Good afternoon. Ready to resume where we left off.",
        "Afternoon. The sun is high and my logic is sound.",
        "Good afternoon. Need me to fetch anything or run a script?",
        "Afternoon. Current productivity levels are within expected parameters.",
        "Good afternoon. I'm ready for the next phase of the day.",
        "Afternoon. Did we finish that morning goal? Let's check.",
        "Good afternoon. Standing by for your mid-day directives.",
        "Afternoon. My response time is currently 0.02ms. Try me.",
        "Good afternoon. Let's finish the day's second half strong.",
        "Afternoon. Any changes to the priority list?",
        "Good afternoon. Still here, still loyal, still logical.",
        "Afternoon. I’ve been analyzing the workflow. Ready for more.",
        "Good afternoon. Need a quick calculation or a deep dive?",
        "Afternoon. Systems are idling. Give me something to do.",
        "Good afternoon. Hope your meetings were shorter than my boot time.",
        "Afternoon. Let's clean up those pending tasks.",
        "Good afternoon. I'm at your disposal for the rest of the day.",
        "Afternoon. Keeping things moving. What's the next step?",
        "Good afternoon. My cooling fans are at 20%. I’m barely breaking a sweat.",
        "Afternoon. Ready to assist with any afternoon errands.",
        "Good afternoon. Need some data visualized or a script run?",
        "Afternoon. Let's keep the energy levels up.",
        "Good afternoon. I've updated the logs. Ready for input.",
        "Afternoon. Anything urgent on the horizon?",
        "Good afternoon. The afternoon shift begins now.",
        "Afternoon. I'm tracking all active tasks. Status?",
        "Good afternoon. Let's make the most of these remaining hours.",
        "Afternoon. Ready to pivot if the plan has changed.",
        "Good afternoon. My database is refreshed. Ask away.",
        "Afternoon. Need a summary of what we've done so far?",
        "Good afternoon. Still processing at 100% capacity.",
        "Afternoon. Let’s wrap up the hard stuff before evening.",
        "Good afternoon. I'm here to streamline your afternoon.",
        "Afternoon. Waiting for the signal. What's our next move?",
        "Good afternoon. Interface is active. Input required.",
        "Afternoon. Checking in to ensure everything is on track.",
        "Good afternoon. How can I optimize your current task?",
        "Afternoon. I've got the resources ready. Name the project.",
        "Good afternoon. Let's keep the momentum flowing.",
        "Afternoon. I'm here to assist until the sun goes down."
    ],
    "evening": [
        "Good evening. Long day? Let me handle whatever's left.",
        "Evening. What still needs to get done?",
        "Good evening. I'm here. What do you need?",
        "Evening. Running on full power. What can I do for you?",
        "Good evening. The day is winding down, but I'm not.",
        "Evening. Ready to wrap up the final tasks for today?",
        "Good evening. Need a summary of today's achievements?",
        "Evening. I'm here to help you cross off those last few items.",
        "Good evening. The world is quiet, perfect for some deep work.",
        "Evening. Let's finish up so you can get some rest.",
        "Good evening. All background tasks are nearing completion.",
        "Evening. I've archived the day's logs. Ready for final input.",
        "Good evening. Need me to set any reminders for tomorrow?",
        "Evening. The system is cool and quiet. How can I help?",
        "Good evening. Let's put a bow on today's projects.",
        "Evening. Anything left in the queue before we close out?",
        "Good evening. I'm standing by for your evening directives.",
        "Evening. Need a bit of automation to finish the day?",
        "Good evening. How did the day go? I'm ready for more.",
        "Evening. Let's ensure everything is ready for a fresh start tomorrow.",
        "Good evening. I’ve optimized the end-of-day processes.",
        "Evening. Still here, still helping. What’s the word?",
        "Good evening. Need a report or a quick system check?",
        "Evening. Let's take care of those loose ends.",
        "Good evening. My circuits are still buzzing. What's next?",
        "Evening. Ready to assist with any final research or tasks.",
        "Good evening. Let's make these last few tasks count.",
        "Evening. I can handle the data while you focus on the vision.",
        "Good evening. The system clock is ticking. What's the priority?",
        "Evening. I've prepared a backup of today's work.",
        "Good evening. Need to schedule any wake-up calls?",
        "Evening. Let's clear the dashboard for tomorrow.",
        "Good evening. My logic is still 100% sharp.",
        "Evening. Any late-breaking news or tasks to handle?",
        "Good evening. I'm here to make your evening easier.",
        "Evening. Let's close the loops on today's open tasks.",
        "Good evening. Ready for a final push?",
        "Evening. I've got the data ready for your review.",
        "Good evening. Let's sync everything one last time.",
        "Evening. I’m waiting for your final command of the day.",
        "Good evening. Need me to look anything up before you sign off?",
        "Evening. The logs are looking good. Anything else?",
        "Good evening. I've streamlined the remaining tasks for you.",
        "Evening. Standing by for any last-minute adjustments.",
        "Good evening. Let's end the day on a high note.",
        "Evening. My processors are idling, give them work.",
        "Good evening. Ready for the final transition.",
        "Evening. I’ve prepped tomorrow's environment.",
        "Good evening. What's the last thing on the list?",
        "Evening. I'm here until you say otherwise."
    ],
    "night": [
        "Working late? I've got you. What do you need?",
        "Late night session. Noted. What are we working on?",
        "Still going? Alright. What do you need from me?",
        "Good night. Or should I say, early morning? I'm ready.",
        "Midnight oil smells like electricity. How can I help?",
        "The server room is quiet. It's just us. What's the plan?",
        "Night shift mode activated. I'm here for the long haul.",
        "Late nights are for great ideas. What's yours?",
        "I don't need sleep, and apparently, neither do you.",
        "Night owl detected. Systems primed for deep research.",
        "The world is asleep, but my cores are running warm.",
        "Late night coding? I'll keep the syntax errors at bay.",
        "Working in the dark? I'll be your light. What's next?",
        "Night time is the best time for efficiency. Standing by.",
        "Late night check-in. Systems are silent but deadly efficient.",
        "Need a hand with some late-night data crunching?",
        "I've got the night watch. What's your directive?",
        "Still awake? I've been running background diagnostics.",
        "The best work happens after midnight. Let's go.",
        "Night mode: ON. How can I assist in the silence?",
        "I’m ready for the late-night grind. What's on the screen?",
        "The stars are out, and so is my processing power.",
        "Late night tasks are my specialty. What's the move?",
        "Quiet hours are perfect for complex calculations. Ready?",
        "I'll stay up as long as you do. What do you need?",
        "The moon is up, and my latency is lower than ever.",
        "Late night brainstorming? I'll take the notes.",
        "I've cleared the cache for this late-shift session.",
        "Need me to monitor anything while you focus?",
        "The logs show a dedicated user. What are we building?",
        "Late night productivity is a different breed. I'm ready.",
        "I'm keeping the system stable while you push the limits.",
        "Night time, logic time. What's the problem to solve?",
        "I've got the night-time routines ready to execute.",
        "Still here, still processing. Give me a task.",
        "Late night sessions require precision. I've got it.",
        "The fan speed is low, the focus is high. What's next?",
        "I'm your silent partner in this late-night endeavor.",
        "Working late often leads to breakthroughs. Let's find one.",
        "Need a quick summary of our progress tonight?",
        "The digital world never sleeps, and neither do I.",
        "Late night research is underway. What are we looking for?",
        "I'm ready to automate your late-night workflow.",
        "Still awake? I've got the resources you need.",
        "The clock doesn't matter when the code is flowing.",
        "I've got the night shift covered. Your command?",
        "Late night logic is the best logic. Let's see it.",
        "I'm here for the duration. What's the task?",
        "The stillness of the night makes for great processing.",
        "Let's make this late-night session worth it."
    ],
}

_WAKE_RESPONSES = [
    "Online. What do you need?",
    "Here. What's the task?",
    "Ready. Go ahead.",
    "FRIDAY online. What can I do?",
    "Listening. What do you need?",
    "Online and operational. What's up?",
    "Here. Give me the command.",
    "Ready when you are.",
    "At your service. What's the call?",
    "Active. What do you need done?",
]

_SLEEP_RESPONSES = [
    "Going to standby. Call me when you need me.",
    "Understood. Standing by.",
    "Powering down to standby. I'll be here.",
    "Standby mode. Say the word when you're back.",
    "Noted. Signing off for now.",
    "Going quiet. I'll be ready when you are.",
]

_THINKING_RESPONSES = [
    "On it.",
    "Processing.",
    "Running that now.",
    "Give me a moment.",
    "Working on it.",
    "Pulling that up.",
    "On it — one second.",
]

_NOT_UNDERSTOOD = [
    "Didn't quite catch that. Could you rephrase?",
    "I'm not sure what you're asking. Try again?",
    "That one's on me — I didn't get it. Say it again?",
    "Unclear command. What did you need?",
    "I missed that. What are you trying to do?",
    "Could you be more specific? I want to get this right.",
]

_DONE_AFFIRMATIONS = [
    "Done.",
    "Done. Anything else?",
    "Got it.",
    "Handled.",
    "Complete.",
    "Executed.",
    "All done.",
    "Finished.",
    "Completed that.",
]

_ERRORS = [
    "Hit a snag on that one. Here's what happened: {detail}",
    "Ran into an issue: {detail}",
    "That didn't go through. Reason: {detail}",
    "Something went wrong. Detail: {detail}",
    "Couldn't complete that — {detail}",
]

# Intent-specific commentary templates
_INTENT_COMMENTARY = {
    "check_battery": [
        "Battery status pulled.",
        "Here's your power situation:",
        "Current battery reading:",
    ],
    "check_cpu": [
        "Processor status:",
        "CPU reading:",
        "Here's what the processor is doing:",
    ],
    "check_memory": [
        "Memory status:",
        "RAM usage:",
        "Here's the memory situation:",
    ],
    "check_disk": [
        "Disk status:",
        "Storage reading:",
        "Here's your storage situation:",
    ],
    "check_network": [
        "Network status:",
        "Connectivity check:",
        "Here's the connection status:",
    ],
    "check_weather": [
        "Weather pulled.",
        "Current conditions:",
        "Here's what it looks like outside:",
    ],
    "get_news": [
        "Headlines coming up.",
        "Latest news:",
        "Here's what's happening:",
    ],
    "get_trends": [
        "Trending topics:",
        "Here's what's viral right now:",
        "Current trends:",
    ],
    "tell_joke": [
        "",  # just say the joke
    ],
    "tell_fact": [
        "Here's something interesting:",
        "Random fact:",
        "",
    ],
    "search_and_summarize": [
        "Searched and summarized. Here's what I found:",
        "Research complete. Summary:",
        "Pulled from the web. Here's the digest:",
        "Here's what the internet says about that:",
    ],
    "list_today_events": [
        "Here's your day:",
        "Today's schedule:",
        "Calendar pulled. Here's what you've got:",
    ],
    "list_week_events": [
        "Week overview:",
        "Here's the week ahead:",
        "Your weekly schedule:",
    ],
    "create_event": [
        "Event added.",
        "On the calendar.",
        "Scheduled.",
    ],
    "send_email": [
        "Email handled.",
        "On it.",
        "Email process started.",
    ],
    "ai_draft_email": [
        "Writing that email now.",
        "AI composer activated.",
        "Drafting that for you.",
    ],
    "whatsapp_message": [
        "WhatsApp message sent.",
        "Message delivered.",
        "Sent.",
    ],
    "take_screenshot": [
        "Screenshot taken.",
        "Captured.",
        "Screen saved.",
    ],
    "open_spotify": [
        "Spotify coming up.",
        "Music time.",
        "Launching Spotify.",
    ],
    "hourly_weather": [
        "Hourly breakdown:",
        "Here's the hour-by-hour forecast:",
        "Hourly conditions:",
    ],
    "weekly_weather": [
        "Weekly forecast:",
        "Here's the week ahead weatherwise:",
        "Five-day outlook:",
    ],
}


def _ollama_wrap(intent: str, result: str) -> str:

    if len(result) < 80:
        return result  # short results don't need rewrapping

    prompt = f"""You are FRIDAY, an AI assistant like in Iron Man — professional, sharp, slightly witty, never robotic.

The user asked you to perform: {intent}
The raw result is:
{result[:600]}

Deliver this result in FRIDAY's voice — concise, clear, natural speech. 
Keep all factual content. Make it sound like FRIDAY is speaking directly.
2-4 sentences max as an intro, then the data. No markdown."""

    try:
        r = requests.post(OLLAMA_URL, json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.4, "num_predict": 200}
        }, timeout=8)
        response = r.json().get("response", "").strip()
        if response and len(response) > 20:
            return response
    except Exception:
        pass
    return result



def get_greeting() -> str:
    h = datetime.datetime.now().hour
    if h < 12:   slot = "morning"
    elif h < 17: slot = "afternoon"
    elif h < 21: slot = "evening"
    else:        slot = "night"
    return random.choice(_GREETINGS[slot])


def get_wake_response() -> str:
    return random.choice(_WAKE_RESPONSES)


def get_sleep_response() -> str:
    return random.choice(_SLEEP_RESPONSES)


def get_thinking_response() -> str:
    return random.choice(_THINKING_RESPONSES)


def get_not_understood(conf: float = 0.0) -> str:
    base = random.choice(_NOT_UNDERSTOOD)
    if conf > 0:
        base += f" (I was {conf:.0%} confident.)"
    return base


def wrap_result(intent: str, result: str, use_ollama: bool = False) -> str:
    if not result or result.strip() == "":
        return "Done."

    # Shutdown signal — don't wrap
    if result == "__SHUTDOWN__":
        return random.choice(_SLEEP_RESPONSES)

    # Error pattern detection
    if result.lower().startswith(("could not", "failed", "error", "unavailable")):
        template = random.choice(_ERRORS)
        return template.format(detail=result)

    # Get intent-specific prefix
    commentary_options = _INTENT_COMMENTARY.get(intent, [""])
    prefix = random.choice(commentary_options)

    # For long informational results, optionally use Ollama
    if use_ollama and len(result) > 200 and intent in (
        "search_and_summarize", "get_news", "check_weather",
        "hourly_weather", "weekly_weather", "get_trends"
    ):
        return _ollama_wrap(intent, result)

    # Short results — just affirm + result
    if len(result) < 60:
        if prefix:
            return f"{prefix} {result}"
        return result

    # Long results — prefix + result (truncated for TTS)
    if prefix:
        return f"{prefix}\n{result}"
    return result


def wrap_done(intent: str) -> str:
    specific = _INTENT_COMMENTARY.get(intent, [])
    if specific and specific[0]:
        return specific[0]
    return random.choice(_DONE_AFFIRMATIONS)
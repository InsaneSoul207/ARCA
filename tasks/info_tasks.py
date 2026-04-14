import datetime, random

JOKES = [
  "Why don't scientists trust atoms? Because they make up everything.",
  "I told my computer I needed a break. Now it keeps sending me Kit Kat ads.",
  "Why do programmers prefer dark mode? Because light attracts bugs.",
  "How many programmers does it take to change a lightbulb? None — that's a hardware problem.",
  "A SQL query walks into a bar and asks two tables: 'Can I join you?'",
  "Why was the JavaScript developer sad? He didn't Node how to Express himself.",
  "There are 10 types of people: those who understand binary and those who don't.",
  "Why do Java developers wear glasses? Because they don't C#.",
  "An algorithm walks into a bar. 'What'll it be?' asks the bartender. 'Depends on the input,' says the algorithm.",
  "I tried to write a joke about recursion, but I tried to write a joke about recursion.",
  "A programmer's partner: 'Go to the store, get milk. If they have eggs, get a dozen.' They came back with 12 milks.",
  "Why did the developer go broke? Because they used up all their cache.",
]

FACTS = [
  "An octopus has three hearts, blue blood, and can edit its own RNA — basically a living science fiction creature.",
  "Honey never expires. Archaeologists found 3,000-year-old honey in Egyptian tombs and it was still edible.",
  "A bolt of lightning is five times hotter than the surface of the Sun.",
  "The average human brain generates about 12 to 25 watts of electricity — enough to power an LED.",
  "There are more possible chess game sequences than atoms in the observable universe.",
  "The first computer bug was a literal moth — found in a Harvard Mark II relay in 1947.",
  "Bananas are slightly radioactive due to their potassium-40 content.",
  "A neutron star is so dense that a teaspoon of its material would weigh about 10 million tonnes on Earth.",
  "The human eye can distinguish approximately 10 million different colors.",
  "WiFi actually stands for nothing. The term 'Wireless Fidelity' was invented after the fact as a backronym.",
]

HELP_TEXT = """ARCA — Command Reference
════════════════════════════════
SYSTEM
open browser / calculator / notepad / task manager
take a screenshot   check battery / cpu / memory / disk / network
volume up / down / mute   lock screen / sleep pc / restart / shutdown

SPOTIFY
open spotify   play music   pause spotify
next song / previous song / skip this song
like this song   play [song name]

APPS
open whatsapp / discord / telegram / word / excel / vscode
(any installed app by name)

WEB & SEARCH
search and summarize [topic]   research [topic]
bbc news / times of india / reuters   what is trending
check weather / hourly forecast / weather this week

WHATSAPP
send a whatsapp to [name] saying [message]

EMAIL
send email to [name] about [topic]
draft an email asking for [topic]
write a professional email to [name]

CALENDAR
what are my meetings today / this week
add a meeting tomorrow at 3pm
when am I free today   delete the [event name] meeting

FILES
find my [filename]   open my [filename]   show recent files
read the screen   read clipboard image

PRODUCTIVITY
start a timer for [N] minutes   stop the timer
take a note [text]   show notes   clear notes
set a reminder to [task]

INFO
what time is it   what is today's date
tell me a joke   tell me a fact
start monitoring   monitoring status

Say ALPHA to activate · Say GOODBYE to end session"""

def tell_time() -> str:
  now = datetime.datetime.now()
  return f"It's {now.strftime('%I:%M %p')}."


def tell_date() -> str:
  now = datetime.datetime.now()
  return f"Today is {now.strftime('%A, %d %B %Y')}."


def tell_joke() -> str:
  joke = random.choice(JOKES)
  return joke


def tell_fact() -> str:
  fact = random.choice(FACTS)
  return fact


def greet() -> str:
  h = datetime.datetime.now().hour
  greetings = {
      "morning": [
          "Good morning. All systems operational. What do you need?",
          "Morning. I've run a quick diagnostic — everything checks out. Ready when you are.",
          "Good morning. What's on the agenda today?",
          "Morning. FRIDAY online. What shall we tackle first?",
      ],
      "afternoon": [
          "Good afternoon. What can I do for you?",
          "Afternoon. Still sharp, still here. What do you need?",
          "Good afternoon. Ready and waiting. What's next?",
      ],
      "evening": [
          "Good evening. Long day? Let me handle whatever's left.",
          "Evening. What still needs to get done?",
          "Good evening. Running on full power. What do you need?",
      ],
      "night": [
          "Working late? I've got you. What do you need?",
          "Late night session. What are we working on?",
          "Still going? Alright. What do you need from me?",
      ],
  }
  if h < 12:   slot = "morning"
  elif h < 17: slot = "afternoon"
  elif h < 21: slot = "evening"
  else:        slot = "night"

  return random.choice(greetings[slot])


def goodbye() -> str:
  return "__SHUTDOWN__"


def show_help() -> str:
  return HELP_TEXT
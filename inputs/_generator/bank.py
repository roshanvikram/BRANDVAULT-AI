"""Shared, realistic building blocks for the test inputs.

Every sentence carries the issue tags it should trigger, so each generated file's
expected result follows from how it was built. Brand truth (NOVA TECH demo):
price ₹79,999; 45 TOPS; up to 18 hours battery; 2-year warranty; the NovaSleeve
pre-order bonus expired in 2024; banned terms "world's fastest",
"10x faster than every competitor", "cheap" and "budget laptop".
"""

CITIES = ["Bengaluru", "Mumbai", "Delhi", "Chennai", "Hyderabad", "Pune", "Kolkata", "Ahmedabad", "Kochi", "Jaipur",
          "Lucknow", "Chandigarh", "Indore", "Coimbatore", "Bhubaneswar"]
FESTIVALS = ["Diwali", "Pongal", "Onam", "Holi", "Eid", "Christmas", "Navratri", "Durga Puja", "Republic Day",
             "Independence Day", "Ganesh Chaturthi", "Baisakhi"]
AUDIENCES = ["students", "creators", "developers", "small business owners", "enterprise IT teams", "designers",
             "data analysts", "consultants", "researchers", "video editors"]

# (sentence, tags)
CLEAN = [
    ("The NovaBook AI Pro 16 is available at ₹79,999 at authorised retailers.", []),
    ("Up to 18 hours of battery on mixed productivity workloads.", []),
    ("The NovaCore N10 AI Engine delivers 45 TOPS of sustained AI performance.", []),
    ("Every unit includes a 2-Year On-Site Limited Hardware Warranty.", []),
    ("Visit a NovaTech experience store in {city} to try it in person.", []),
    ("Designed for {audience} who need quiet, dependable performance.", []),
    ("Order online and collect it from your nearest store.", []),
    ("The display is factory-calibrated for accurate colour.", []),
    ("Talk to our enterprise team about volume deployments.", []),
    ("Now shipping across India.", []),
    ("Precise, calm and built for long working days.", []),
    ("Backed by NovaTech service centres in every major city.", []),
    ("Meet the NovaBook AI Pro 16.", []),
    ("Your work, handled locally with on-device AI.", []),
    ("A full-size keyboard with a quiet, steady typing feel.", []),
]

PRICES_WRONG = ["69,999", "72,999", "74,999", "64,999", "71,499", "75,000", "77,777", "59,999", "67,999", "76,500"]

VIOLATIONS = {
    "price_conflict": [
        ("This {festival}, take it home for just ₹{price}.", ["price_conflict"]),
        ("Rs.{price}/- only at our {city} store.", ["price_conflict"]),
        ("INR {price_plain} special price for {audience}.", ["price_conflict"]),
        ("Price drop alert: ₹ {price} this weekend.", ["price_conflict"]),
        ("Exchange your old laptop and pay only ₹{price}.", ["price_conflict"]),
    ],
    "superlative": [
        ("The fastest laptop in India.", ["superlative"]),
        ("India's #1 AI laptop.", ["superlative"]),
        ("The most powerful AI laptop ever made.", ["superlative"]),
        ("The best laptop money can buy.", ["superlative"]),
        ("Unbeatable performance in every task.", ["superlative"]),
        ("Asia's number one AI notebook.", ["superlative"]),
    ],
    "comparative": [
        ("2x faster than the MacBook Air in AI workloads.", ["comparative"]),
        ("Beats Dell and HP on battery life.", ["comparative"]),
        ("Outperforms every Windows laptop in its class.", ["comparative"]),
        ("Leaves the competition behind.", ["comparative"]),
        ("Faster than any rival in its price range.", ["comparative"]),
        ("3x faster than Lenovo's ThinkPad on AI tasks.", ["comparative"]),
    ],
    "terminology": [
        ("A cheap way to get serious AI performance.", ["terminology"]),
        ("It is cheaper than you think.", ["terminology"]),
        ("The budget laptop that handles AI with ease.", ["terminology"]),
        ("Not your usual cheap AI device.", ["terminology"]),
    ],
    "superlative+terminology": [
        ("The world's fastest AI laptop is here.", ["superlative", "terminology"]),
        ("World’s fastest AI laptop, now shipping.", ["superlative", "terminology"]),
    ],
    "comparative+terminology": [
        ("10x faster than every competitor.", ["comparative", "terminology"]),
    ],
    "tone": [
        ("Hurry!! Stocks are running out!!", ["tone"]),
        ("OMG this laptop is INSANE 🔥", ["tone"]),
        ("HUGE SALE — TODAY ONLY", ["tone"]),
        ("Don't miss this!! Grab yours now!!", ["tone"]),
        ("This thing is CRAZY fast, not even joking", ["tone"]),
    ],
    "outdated": [
        ("Pre-order now and get a complimentary NovaSleeve.", ["outdated"]),
        ("Claim your free NovaSleeve pre-order bonus today.", ["outdated"]),
        ("Last chance to collect your NovaSleeve pre-order gift.", ["outdated"]),
    ],
    "needs_review": [
        ("A game-changing machine for modern work.", ["needs_review"]),
        ("Cutting-edge thermals keep it cool under load.", ["needs_review"]),
        ("Unmatched build quality from a brand you trust.", ["needs_review"]),
        ("An industry-leading keyboard for long sessions.", ["needs_review"]),
        ("A revolutionary way to work with AI.", ["needs_review"]),
        ("No-cost EMI from ₹6,667/month on select cards.", ["needs_review"]),
    ],
    "fact_conflict": [
        ("Up to {hours} hours of battery life.", ["fact_conflict"]),
        ("The NovaCore N10 delivers {tops} TOPS of AI performance.", ["fact_conflict"]),
        ("Comes with a {years}-year warranty.", ["fact_conflict"]),
        ("All-day battery: {hours} hours on a single charge.", ["fact_conflict"]),
    ],
}

WRONG_HOURS = [20, 22, 24, 26, 30, 36]
WRONG_TOPS = [40, 48, 50, 55, 60]
WRONG_YEARS = [1, 3, 5]

CHANNEL_OPENERS = {
    "instagram": "",
    "whatsapp": "Hi! ",
    "email": "Dear customer,\n\n",
    "sms": "NovaTech: ",
    "linkedin": "",
    "store banner": "",
    "press release": "BENGALURU — ",
    "retailer listing": "",
    "google ad": "",
    "newsletter": "This month at NovaTech:\n\n",
}


def fill(template: str, rnd) -> str:
    price = rnd.choice(PRICES_WRONG)
    return template.format(
        city=rnd.choice(CITIES), festival=rnd.choice(FESTIVALS), audience=rnd.choice(AUDIENCES),
        price=price, price_plain=price.replace(",", ""), hours=rnd.choice(WRONG_HOURS),
        tops=rnd.choice(WRONG_TOPS), years=rnd.choice(WRONG_YEARS))

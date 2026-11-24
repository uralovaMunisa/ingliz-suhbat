from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def get_level_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton("A1 - Beginner 🟢", callback_data="level:A1"),
            InlineKeyboardButton("A2 - Elementary 🟡", callback_data="level:A2"),
        ],
        [
            InlineKeyboardButton("B1 - Intermediate 🟠", callback_data="level:B1"),
            InlineKeyboardButton("B2 - Upper-Int 🔵", callback_data="level:B2"),
        ],
        [
            InlineKeyboardButton("C1 - Advanced 🟣", callback_data="level:C1"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_goal_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton("🗣 Daily Conversation", callback_data="goal:Daily conversation"),
            InlineKeyboardButton("💼 Work & Business", callback_data="goal:Work & Career"),
        ],
        [
            InlineKeyboardButton("✈️ Travel & Living Abroad", callback_data="goal:Travel"),
            InlineKeyboardButton("🎓 IELTS / Exam Prep", callback_data="goal:IELTS & Exams"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_topic_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("☕ Hobbies & Free Time", callback_data="topic:hobbies")],
        [InlineKeyboardButton("✈️ Travel & Dream Trips", callback_data="topic:travel")],
        [InlineKeyboardButton("🎬 Movies, Music & Books", callback_data="topic:entertainment")],
        [InlineKeyboardButton("🚀 Future Goals & Career", callback_data="topic:career")],
    ]
    return InlineKeyboardMarkup(keyboard)

def get_correction_keyboard(mistake_id: int) -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("🇺🇿 Explain in Uzbek / O'zbekcha tushuntirish", callback_data=f"uz_exp:{mistake_id}")]
    ]
    return InlineKeyboardMarkup(keyboard)


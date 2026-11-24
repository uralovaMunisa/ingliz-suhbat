import pytest
from services.parser import ResponseParser

def test_extract_mistakes_single():
    sample_response = (
        "Sounds like a great trip! 🍎 What fruits did you buy?\n\n"
        "✏️ **Correction:**\n"
        "- ❌ *Yesterday I go to the market and buy many fruits.* → ✅ *Yesterday I **went** to the market and **bought** many fruits.*\n"
        "- 💡 Use the past simple for finished actions: go → went, buy → bought.\n\n"
        "📚 **New phrase:** \"to do the shopping\" = to buy things you need. *Example: I do the shopping every Saturday.*"
    )

    mistakes = ResponseParser.extract_mistakes(sample_response)
    assert len(mistakes) == 1
    assert "Yesterday I go to the market" in mistakes[0]["original"]
    assert "Yesterday I went to the market" in mistakes[0]["corrected"] or "Yesterday I **went**" in mistakes[0]["corrected"]
    assert "past simple" in mistakes[0]["explanation"]

    assert ResponseParser.has_corrections(sample_response) is True


def test_extract_mistakes_multiple():
    sample_response = (
        "I love traveling too! Have you ever flown abroad?\n\n"
        "✏️ **Correction:**\n"
        "- ❌ *She don't likes tea* → ✅ *She doesn't like tea*\n"
        "- 💡 For third person singular (she/he/it), use 'doesn't' + base verb.\n"
        "- ❌ *I am agree with you* → ✅ *I agree with you*\n"
        "- 💡 'Agree' is a verb, not an adjective, so do not use 'am'.\n"
    )

    mistakes = ResponseParser.extract_mistakes(sample_response)
    assert len(mistakes) == 2
    assert "She don't likes tea" in mistakes[0]["original"]
    assert "She doesn't like tea" in mistakes[0]["corrected"]
    assert "I am agree with you" in mistakes[1]["original"]
    assert "I agree with you" in mistakes[1]["corrected"]


def test_extract_mistakes_none():
    sample_response = (
        "That's fantastic! 👏 What are you planning to do this weekend?\n\n"
        "✏️ **Correction:**\n"
        "- 👏 Perfect sentence! No mistakes.\n"
    )

    mistakes = ResponseParser.extract_mistakes(sample_response)
    assert len(mistakes) == 0


def test_extract_vocabulary():
    sample_response = (
        "Sounds fun! What movie did you watch?\n\n"
        "✏️ **Correction:**\n"
        "- 👏 Perfect sentence! No mistakes.\n\n"
        "📚 **New word/phrase:** \"a couch potato\" = a person who spends a lot of time sitting and watching television. *Example: Don't be such a couch potato, let's go outside!*\n"
    )

    vocab = ResponseParser.extract_vocabulary(sample_response)
    assert vocab is not None
    assert vocab["phrase"] == "a couch potato"
    assert "sitting and watching television" in vocab["definition"]
    assert "couch potato" in vocab["example"]


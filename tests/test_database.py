import pytest
import os
import tempfile
import asyncio
from db.database import Database

def test_database_lifecycle():
    async def _run():
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_emma.db")
            db = Database(db_path)
            await db.init_db()

            # 1. User creation and update
            user = await db.get_or_create_user(12345, "testuser", "John")
            assert user["user_id"] == 12345
            assert user["name"] == "John"
            assert user["level"] == "B1"
            assert user["goal"] == "Daily conversation"
            assert user["correction_mode"] == "standard"

            await db.update_user(12345, level="B2", goal="IELTS", correction_mode="strict")
            updated_user = await db.get_user(12345)
            assert updated_user["level"] == "B2"
            assert updated_user["goal"] == "IELTS"
            assert updated_user["correction_mode"] == "strict"

            # 2. Chat history
            await db.add_chat_message(12345, "user", "Hello Emma!")
            await db.add_chat_message(12345, "model", "Hi John! How are you today?")
            history = await db.get_recent_chat_history(12345, limit=10)
            assert len(history) == 2
            assert history[0]["role"] == "user"
            assert history[0]["content"] == "Hello Emma!"
            assert history[1]["role"] == "model"
            assert history[1]["content"] == "Hi John! How are you today?"

            await db.clear_chat_history(12345)
            empty_history = await db.get_recent_chat_history(12345, limit=10)
            assert len(empty_history) == 0

            # 3. Mistakes logging
            m_id = await db.log_mistake(
                12345,
                original="I go yesterday",
                corrected="I went yesterday",
                explanation="Use past tense 'went' for finished actions."
            )
            assert m_id > 0
            mistakes = await db.get_recent_mistakes(12345, limit=5)
            assert len(mistakes) == 1
            assert mistakes[0]["original_text"] == "I go yesterday"
            assert mistakes[0]["corrected_text"] == "I went yesterday"

            await db.update_mistake_uzbek(m_id, "O'tgan zamonda 'go' o'rniga 'went' ishlatiladi.")
            updated_mistake = await db.get_mistake(m_id)
            assert updated_mistake["explanation_uz"] == "O'tgan zamonda 'go' o'rniga 'went' ishlatiladi."

            # 4. Vocabulary logging
            v_id = await db.log_vocabulary(
                12345,
                phrase="call it a day",
                definition="to stop what you are doing",
                example="Let's call it a day and go home."
            )
            assert v_id > 0
            vocab = await db.get_recent_vocabulary(12345, limit=5)
            assert len(vocab) == 1
            assert vocab[0]["phrase"] == "call it a day"

            # 5. Message count tracking
            count1 = await db.increment_message_count(12345)
            count2 = await db.increment_message_count(12345)
            assert count1 == 1
            assert count2 == 2
            await db.reset_message_count(12345)
            user_after_reset = await db.get_user(12345)
            assert user_after_reset["message_count"] == 0

    asyncio.run(_run())

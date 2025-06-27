import pytest
from app.utils.ai_security import sanitize_prompt

@pytest.mark.parametrize("text,expected", [
    ("Accendi le luci", (True, None)),
    ("<script>alert('x')</script>", (False, "Pattern pericoloso rilevato: <script.*?>.*?</script>")),
    ("{{ dangerous }}", (False, "Pattern pericoloso rilevato: \\{\\{.*?\\}\}\")),
    ("os.system('rm -rf /')", (False, "Pattern pericoloso rilevato: (os\\.|subprocess\\.|eval\\(|exec\\()")),
    ("' OR 1=1; --", (False, "Pattern pericoloso rilevato: --|/\\*|\\*/|;")),
    ("A"*501, (False, "Prompt troppo lungo (>500 caratteri)")),
    ("<b>ciao</b>", (False, "Tag HTML non consentiti")),
])
def test_sanitize_prompt(text, expected):
    assert sanitize_prompt(text) == expected

# Test retry logic simulato
from unittest.mock import AsyncMock
import asyncio

class DummyWorker:
    def __init__(self):
        self.called = 0
    async def process_message(self, message_data):
        self.called += 1
        if self.called == 1:
            raise Exception("fail")
        return "ok"

@pytest.mark.asyncio
async def test_retry_logic():
    worker = DummyWorker()
    # Simula retry logic: primo tentativo fallisce, secondo va
    try:
        await worker.process_message({"_retry_count": 0})
    except Exception:
        # Simula retry
        await worker.process_message({"_retry_count": 1})
    assert worker.called == 2 
import re

def sanitize_prompt(text: str):
    """
    Sanitizza il prompt per l'AI: blocca sequenze pericolose, limita la lunghezza, blocca pattern injection.
    Restituisce (True, None) se valido, (False, reason) se bloccato.
    """
    if not isinstance(text, str):
        return False, "Input non stringa"
    if len(text) > 500:
        return False, "Prompt troppo lungo (>500 caratteri)"
    # Blocca pattern injection noti
    dangerous_patterns = [
        r"\{\{.*?\}\}",   # template injection
        r"<script.*?>.*?</script>",  # XSS
        r"(os\.|subprocess\.|eval\(|exec\()",  # python injection
        r"\$\{.*?\}",  # shell injection
        r"[\"\']\s*;",  # SQL injection
        r"--|/\*|\*/|;",  # SQL comment/injection
    ]
    for pat in dangerous_patterns:
        if re.search(pat, text, re.IGNORECASE):
            return False, f"Pattern pericoloso rilevato: {pat}"
    # Blocca tag HTML/script
    if re.search(r"<.*?>", text):
        return False, "Tag HTML non consentiti"
    return True, None 
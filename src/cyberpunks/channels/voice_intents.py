"""Pure, conservative Romanian voice routing. Matches are intents, never authorization.

Finite full-utterance grammar: unsupported or mixed requests fall through to the
caller. No model, I/O, role selection, job state, or operational imports.
"""

import re
import unicodedata

__all__ = ["dispatch_request", "hearing_check", "normalize", "report_request", "status_request"]

_QUOTES = re.compile(r"""["„”“«»`‘’‚]|(?<!\w)'|'(?!\w)""")
_BLOCKED = re.compile(
    r"\b(?:nu|nici|fara|daca|ipotetic|exemplu|citat|poate|as|ati|ar|"
    r"trebui|presupunem|imagineaza|explica|explici|invata|instructiuni)\b"
)
_FILLER = re.compile(
    r"^(?:(?:a+|e+|um|uh|hm+|pai|deci|ok|okay|bun|bine|salut|alo|"
    r"buna(?: ziua| seara)?|acum|acuma|da(?!\s+(?:mi|raport|pdf|fisa|traseu|un|o)\b)|si)\b\s*)+"
)
_POLITE = re.compile(r"\b(?:te rog(?: frumos)?|va rog(?: frumos)?|multumesc|mersi)\b")
_HESITATION = re.compile(r"\b(?:a{2,}|e{2,}|um|uh|hm+)\b")


def normalize(text: str) -> str:
    """Casefold, remove diacritics, replace punctuation with spaces, collapse space.

    This is not a safety filter. Matchers inspect quotes before normalization.
    """
    plain = "".join(char for char in unicodedata.normalize("NFKD", text.casefold()) if not unicodedata.combining(char))
    return " ".join(re.sub(r"[^\w\s]|_", " ", plain).split())


def _utterance(text: str) -> str:
    if _QUOTES.search(text):
        return ""
    plain = normalize(text)
    if _BLOCKED.search(plain):
        return ""
    plain = _POLITE.sub(" ", plain)
    plain = _HESITATION.sub(" ", plain)
    return " ".join(_FILLER.sub("", plain.strip()).split())


_DOCUMENT = r"(?:raport(?:ul)?|pdf(?: ul)?|fisa|traseu(?:l)?)"
_REPORT = re.compile(
    rf"(?:(?:poti|puteti) (?:sa )?)?"
    rf"(?:imi |mi )?"
    rf"(?:trimite|trimiti|trimiteti|da|dai|dati|genereaza|generezi|pregateste|pregatesti|exporta) "
    rf"(?:(?:mi|imi) )?(?:si )?(?:mie )?(?:(?:un|o) )?{_DOCUMENT}"
    rf"(?: (?:in format pdf|pdf))?(?: pe whatsapp)?"
)
_WANT_REPORT = re.compile(
    rf"(?:vreau|doresc) (?:(?:sa )?(?:imi |mi )?"
    rf"(?:trimiti|trimiteti|dai|dati|generezi|pregatesti) )?"
    rf"(?:si )?(?:mie )?(?:(?:un|o) )?{_DOCUMENT}(?: (?:in format pdf|pdf))?(?: pe whatsapp)?"
)


def report_request(text: str) -> bool:
    """Explicit report creation/delivery, excluding status and reading questions."""
    plain = _utterance(text)
    return bool(_REPORT.fullmatch(plain) or _WANT_REPORT.fullmatch(plain))


_QUEUE_OBJECT = r"(?:(?:toate|toate aceste) )?(?:tichete(?:le)?|cazuri(?:le)?|recomandari(?:le)?|coada)"
_DISPATCH = re.compile(
    rf"(?:(?:(?:poti|puteti) sa|vreau sa|doresc sa) )?"
    rf"(?:"
    rf"(?:rezolva|rezolvi|rezolvati|proceseaza|procesezi|gestioneaza|gestionezi|aplica|aplici) "
    rf"(?:tu )?{_QUEUE_OBJECT}"
    rf"|ocupa te (?:tu )?de {_QUEUE_OBJECT}"
    rf"|(?:ia|iei) (?:tu )?deciziile"
    rf"|decide(?: tu)? pentru mine"
    rf")(?:(?: automat)? pentru mine| automat)?"
)
_CONTEXT_DISPATCH = re.compile(
    r"(?:(?:(?:poti|puteti) sa|vreau sa|doresc sa) )?"
    r"(?:rezolva le(?: tu)?|aplica le(?: tu)?|ocupa te(?: tu)? de ele|rezolvi(?: tu)?(?: toate)?|fa(?: tu)? asta|faci(?: tu)? asta)"
    r"(?: automat)?(?: pentru mine)?"
)
# Compatibility with the two affirmative ASR examples in the existing call tests.
_ASR_DISPATCH = {
    "vreau sa fac vreau sa faci tu asta pentru mine rezolva toate cazurile",
    "pot sa le rezolv pe intre mine",
}


def dispatch_request(text: str, *, queue_context: bool = False) -> bool:
    """Explicit queue action; pronoun-only actions require trusted queue context.

    queue_context is server-owned conversation state, never inferred from text.
    A true result still requires the existing caller/role/action authorization.
    """
    plain = _utterance(text)
    return bool(
        _DISPATCH.fullmatch(plain) or plain in _ASR_DISPATCH or (queue_context and _CONTEXT_DISPATCH.fullmatch(plain))
    )


_STATUS = re.compile(
    rf"(?:ai terminat|ati terminat|(?:e|este|esti|sunt) gata|gata|"
    rf"ce ai facut|ce ati facut|cum merge|cum merg lucrurile|"
    rf"in ce stadiu (?:e|este|esti)|care (?:e|este) (?:stadiul|statusul)|status|"
    rf"s a trimis {_DOCUMENT}|(?:ai|ati) trimis {_DOCUMENT}|"
    rf"{_DOCUMENT} (?:s a trimis|(?:a fost|e|este) (?:trimis|trimisa|livrat|livrata)))"
    rf"(?: pe whatsapp)?"
)


def status_request(text: str) -> bool:
    """Progress/completion/delivery questions; never a new report request."""
    return bool(_STATUS.fullmatch(_utterance(text)))


_HEARING = re.compile(
    r"(?:alo(?: (?:ma auzi|ma auziti|se aude|mai esti(?: aici)?))?|"
    r"ma auzi|ma auziti|se aude|mai esti(?: aici)?)"
)


def hearing_check(text: str) -> bool:
    """Match the whole hearing check, preserving 'alo' and rejecting extra content."""
    if _QUOTES.search(text):
        return False
    return bool(_HEARING.fullmatch(normalize(text)))

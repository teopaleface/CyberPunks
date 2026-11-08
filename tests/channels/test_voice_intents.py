"""Synthetic utterances only; pure helpers need no operational fixtures or services."""

import pytest

from cyberpunks.channels.voice_intents import (
    dispatch_request,
    hearing_check,
    normalize,
    report_request,
    status_request,
)


@pytest.mark.parametrize(
    "text, expected",
    [
        ("  ÎMI dai, ȘI mie RAPORTUL?!  ", "imi dai si mie raportul"),
        ("Poți să-mi trimiți fișa pe WhatsApp?", "poti sa mi trimiti fisa pe whatsapp"),
        ("ŞŢ ĂÂÎ şţ ăâî", "st aai st aai"),
        ("PDF-ul\n\t trimis…", "pdf ul trimis"),
        ("", ""),
    ],
)
def test_normalize(text, expected):
    assert normalize(text) == expected
    assert normalize(normalize(text)) == expected


@pytest.mark.parametrize(
    "text",
    [
        "Îmi dai și mie raportul?",
        "Poti sa-mi trimiti fisa pe WhatsApp?",
        "Trimite-mi raportul pe WhatsApp",
        "Îmi trimiți PDF-ul?",
        "Vreau raportul",
        "Ăăă, păi, poți să-mi trimiți, te rog, fișa pe WhatsApp?!",
        "Bună ziua! Îmi dai raportul, te rog frumos?",
        "Da, trimite-mi raportul.",
        "Generează raportul PDF",
        "Doresc să-mi trimiți raportul în format PDF pe WhatsApp",
        "Trimite traseul",
        "Pregătește o fișă",
        "Vă rog, trimiteți raportul.",
        "Alo, trimite raportul",
        "Vreau să îmi dai și mie raportul",
    ],
)
def test_report_requests(text):
    assert report_request(text)
    assert not dispatch_request(text, queue_context=True)
    assert not status_request(text)
    assert not hearing_check(text)


@pytest.mark.parametrize(
    "text",
    [
        "Aplică recomandările",
        "Ia deciziile pentru mine",
        "Ocupă-te de tichete",
        "Rezolvă toate cazurile",
        "Procesează tichetele",
        "Gestionează coada",
        "Păi, aplică, te rog, toate recomandările pentru mine!",
        "Poți să rezolvi toate tichetele pentru mine?",
        "Vreau să aplici recomandările",
        "Decide tu pentru mine",
        "Da, rezolvă toate cazurile!",
        "Păi, vreau să fac-- vreau să faci tu asta pentru mine, rezolvă toate cazurile.",
        "Pot să le rezolv pe între mine?",
    ],
)
def test_explicit_queue_requests(text):
    assert dispatch_request(text)
    assert dispatch_request(text, queue_context=True)
    assert not report_request(text)
    assert not status_request(text)


@pytest.mark.parametrize(
    "text",
    [
        "Rezolvă-le",
        "Fă tu asta pentru mine",
        "Ăă, rezolvă-le, te rog!",
        "Poți să faci tu asta pentru mine?",
    ],
)
def test_pronoun_actions_require_server_queue_context(text):
    assert not dispatch_request(text)
    assert dispatch_request(text, queue_context=True)
    assert not report_request(text)


@pytest.mark.parametrize(
    "text",
    [
        "Ai terminat?",
        "Ce ai făcut?",
        "Cum merge?",
        "În ce stadiu e?",
        "S-a trimis raportul?",
        "Ăă, ai terminat?",
        "Raportul a fost trimis?",
        "Ai trimis PDF-ul pe WhatsApp?",
        "S-a trimis fișa?",
        "Status?",
        "E gata?",
    ],
)
def test_status_never_starts_a_report_or_dispatch(text):
    assert status_request(text)
    assert not report_request(text)
    assert not dispatch_request(text, queue_context=True)
    assert not hearing_check(text)


@pytest.mark.parametrize(
    "text",
    [
        "Alo! Mai ești?",
        "Mă auzi?",
        "ALO, MA AUZI?!",
        "Mai ești aici?",
        "Alo",
        "Mă auziți?",
        "Se aude?",
    ],
)
def test_whole_hearing_checks(text):
    assert hearing_check(text)
    assert not report_request(text)
    assert not dispatch_request(text, queue_context=True)
    assert not status_request(text)


@pytest.mark.parametrize(
    "text",
    [
        "",
        "...",
        "da",
        "Da!",
        "Bine",
        "Sigur",
        "Nu trimite raportul",
        "Nu aplica recomandările",
        "Nu rezolva-le",
        "Nu ai terminat?",
        "Nici să trimiți raportul",
        "Dacă vreau raportul?",
        "Dacă aplici recomandările?",
        "Poate rezolvi tichetele",
        "Aș vrea raportul",
        "Ar trebui să aplici recomandările",
        'A spus "trimite raportul"',
        '"Aplică recomandările"',
        "„Rezolvă-le”",
        "'Trimite raportul'",
        "«Mă auzi?»",
        "`Aplică recomandările`",
        "Cum rezolv toate cazurile?",
        "Cum trimit raportul?",
        "Explică-mi cum să aplic recomandările",
        "De ce îmi trimiți raportul?",
        "De ce vreau raportul?",
        "Vreau să citesc raportul",
        "Citește raportul",
        "Ce scrie în fișă?",
        "Raportul spune să aplici recomandările",
        "Vreau să știu dacă s-a trimis raportul",
        "Ai terminat raportul și trimite-l",
        "Mă auzi și rezolvă-le",
        "Rezolvă-le fără confirmare",
        "Decide",
        "Trimite raportul și aplică recomandările",
        "Aplică recomandările dar nu acum",
        "Rezolvă factura",
        "Fă tu asta pentru mine și șterge datele",
    ],
)
def test_unsafe_ambiguous_or_unrelated_utterances_fall_through(text):
    assert not report_request(text)
    assert not dispatch_request(text, queue_context=True)
    assert not status_request(text)
    assert not hearing_check(text)


@pytest.mark.parametrize(
    "text",
    [
        "Alo! Mai ești? Trimite raportul",
        "Mă auzi? Am rămas fără curent",
        "Clientul mă auzi?",
        "Mai ești dispecer?",
        "Nu mă auzi?",
        "Alo alo alo",
    ],
)
def test_hearing_check_does_not_swallow_arbitrary_content(text):
    assert not hearing_check(text)


@pytest.mark.parametrize(
    "command",
    [
        "Trimite raportul",
        "Aplică recomandările",
        "Rezolvă-le",
        "Fă tu asta pentru mine",
        "Ai terminat",
        "Mă auzi",
    ],
)
@pytest.mark.parametrize(
    "wrapper",
    [
        "Nu {}",
        '"{}"',
        "„{}”",
        "'{}'",
        "Dacă {}",
        "Ipotetic {}",
        "De exemplu {}",
        "Cum pot să {}",
        "De ce {}",
    ],
)
def test_guard_matrix_preserves_safety_even_with_queue_context(command, wrapper):
    text = wrapper.format(command)
    assert not report_request(text)
    assert not dispatch_request(text, queue_context=True)
    assert not status_request(text)
    assert not hearing_check(text)


def test_imperative_give_report_is_not_mistaken_for_yes_filler():
    assert report_request("Dă-mi raportul pe WhatsApp.")
    assert report_request("Dă un raport PDF, te rog.")
    assert not report_request("Da")


def test_contextual_pronouns_keep_explicit_automatic_requests():
    for phrase in ("Rezolvă-le tu automat", "Aplică-le", "Ocupă-te de ele"):
        assert dispatch_request(phrase, queue_context=True)
        assert not dispatch_request(phrase)

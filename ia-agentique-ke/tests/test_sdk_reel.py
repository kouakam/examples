"""Vérifie le chemin « mode réel » avec le vrai SDK Anthropic, sans réseau.

Un transport HTTP factice joue le rôle de l'API : on contrôle ainsi que le
SDK accepte nos paramètres (outils stricts, cache, repli serveur) et que la
boucle sait relire ses propres réponses lors du tour suivant.
"""

import json

import pytest

anthropic = pytest.importorskip("anthropic")
httpx = pytest.importorskip("httpx2")  # client HTTP du SDK anthropic 1.x et plus

from noyau import Journal, approbation_automatique  # noqa: E402


def _message(contenu, stop):
    return {"id": "msg_test", "type": "message", "role": "assistant", "model": "claude-opus-5-5",
            "content": contenu, "stop_reason": stop, "stop_sequence": None,
            "usage": {"input_tokens": 100, "output_tokens": 20}}


def test_cas1_avec_le_vrai_sdk():
    from cas1_service_client import agent as module
    from cas1_service_client.outils import Etat

    requetes = []
    reponses = [
        _message([{"type": "text", "text": "Je lis le ticket."},
                  {"type": "tool_use", "id": "toolu_01", "name": "lire_ticket", "input": {"ticket_id": "T-04"}}],
                 "tool_use"),
        _message([{"type": "text", "text": "Ticket T-04 : politique de retour communiquée."}], "end_turn"),
    ]

    def api_factice(requete: httpx.Request) -> httpx.Response:
        requetes.append({"url": str(requete.url), "entetes": dict(requete.headers),
                         "corps": json.loads(requete.content)})
        return httpx.Response(200, json=reponses[len(requetes) - 1])

    client = anthropic.Anthropic(api_key="cle-de-test", base_url="https://api.test",
                                 http_client=httpx.Client(transport=httpx.MockTransport(api_factice)),
                                 max_retries=0)
    module.ETAT = Etat()
    ag = module.construire(client=client, approbateur=approbation_automatique(False),
                           journal=Journal("test-sdk", silencieux=True))
    r = ag.executer("Traite le ticket T-04.")

    assert r.statut == "termine" and r.jetons_entree == 200
    premier, second = requetes[0]["corps"], requetes[1]["corps"]
    assert premier["model"] == "claude-opus-5-5"
    assert premier["fallbacks"] == "default"
    assert "server-side-fallback-2026-07-01" in requetes[0]["entetes"]["anthropic-beta"]
    assert premier["cache_control"] == {"type": "ephemeral"}
    assert all(o["strict"] for o in premier["tools"])
    # Le second appel renvoie le bloc tool_use de l'assistant puis le tool_result.
    assert second["messages"][1]["content"][1]["type"] == "tool_use"
    resultat = second["messages"][2]["content"][0]
    assert resultat["tool_use_id"] == "toolu_01" and "Quincaillerie Mbarga" in resultat["content"]

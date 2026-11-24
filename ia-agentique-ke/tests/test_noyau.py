"""Tests de la boucle agentique, sans réseau, avec un faux client."""

from types import SimpleNamespace

import pytest

from noyau import Agent, ErreurOutil, Journal, Outil, approbation_automatique


class FauxClient:
    """Rejoue une liste de réponses et mémorise les paramètres reçus."""

    def __init__(self, reponses):
        self.reponses = list(reponses)
        self.appels = []
        self.beta = SimpleNamespace(messages=SimpleNamespace(create=self._creer))

    def _creer(self, **parametres):
        self.appels.append(parametres)
        return self.reponses.pop(0)


def reponse(stop, *blocs):
    return SimpleNamespace(content=list(blocs), stop_reason=stop,
                           usage=SimpleNamespace(input_tokens=10, output_tokens=5))


def texte(t):
    return SimpleNamespace(type="text", text=t)


def outil(nom, entree, ident="toolu_1"):
    return SimpleNamespace(type="tool_use", id=ident, name=nom, input=entree)


def agent(client, outils, **kw):
    return Agent("test", "système", outils, client=client, journal=Journal("test", silencieux=True), **kw)


def addition(a: int, b: int) -> int:
    return a + b


ADDITION = Outil("addition", "Additionne deux entiers.", {"a": {"type": "integer"}, "b": {"type": "integer"}}, addition)


def test_boucle_simple_et_parametres_envoyes():
    client = FauxClient([reponse("tool_use", outil("addition", {"a": 2, "b": 3})), reponse("end_turn", texte("5"))])
    r = agent(client, [ADDITION]).executer("2 + 3 ?")
    assert (r.statut, r.texte, r.etapes) == ("termine", "5", 2)
    assert r.jetons_entree == 20
    p = client.appels[0]
    assert p["model"] == "claude-opus-5-5"
    assert p["tools"][0]["strict"] is True
    assert p["tools"][0]["input_schema"]["additionalProperties"] is False
    assert p["tools"][0]["input_schema"]["required"] == ["a", "b"]
    assert p["cache_control"] == {"type": "ephemeral"}
    # Deuxième appel : l'historique contient la réponse de l'assistant puis le résultat de l'outil.
    second = client.appels[1]["messages"]
    assert second[1]["role"] == "assistant"
    assert second[2]["content"][0] == {"type": "tool_result", "tool_use_id": "toolu_1", "content": "5"}


def test_erreur_outil_renvoyee_au_modele():
    def echoue():
        raise ErreurOutil("client introuvable")

    o = Outil("echoue", "…", {}, echoue)
    client = FauxClient([reponse("tool_use", outil("echoue", {})), reponse("end_turn", texte("ok"))])
    r = agent(client, [o]).executer("x")
    resultat = client.appels[1]["messages"][2]["content"][0]
    assert resultat["is_error"] is True and "introuvable" in resultat["content"]
    assert r.appels_outils[0]["erreur"] is True


def test_outil_sensible_refuse_n_est_pas_execute():
    execute = []
    o = Outil("payer", "…", {}, lambda: execute.append(1), sensible=True)
    client = FauxClient([reponse("tool_use", outil("payer", {})), reponse("end_turn", texte("annulé"))])
    agent(client, [o], approbateur=approbation_automatique(False)).executer("paye")
    assert execute == []
    assert "refusé" in client.appels[1]["messages"][2]["content"][0]["content"]


def test_appels_paralleles_dans_un_seul_message():
    client = FauxClient([reponse("tool_use", outil("addition", {"a": 1, "b": 1}, "t1"),
                                 outil("addition", {"a": 2, "b": 2}, "t2")), reponse("end_turn", texte("fini"))])
    agent(client, [ADDITION]).executer("x")
    resultats = client.appels[1]["messages"][2]["content"]
    assert [r["content"] for r in resultats] == ["2", "4"]


def test_budget_d_etapes():
    client = FauxClient([reponse("tool_use", outil("addition", {"a": 1, "b": 1}, f"t{i}")) for i in range(3)])
    r = agent(client, [ADDITION], max_etapes=3).executer("boucle")
    assert r.statut == "limite"


@pytest.mark.parametrize("stop, statut", [("refusal", "refus"), ("max_tokens", "tronque")])
def test_arrets_speciaux(stop, statut):
    r = agent(FauxClient([reponse(stop, texte("…"))]), [ADDITION]).executer("x")
    assert r.statut == statut


def test_outil_inconnu():
    client = FauxClient([reponse("tool_use", outil("inexistant", {})), reponse("end_turn", texte("ok"))])
    agent(client, [ADDITION]).executer("x")
    assert client.appels[1]["messages"][2]["content"][0]["is_error"] is True

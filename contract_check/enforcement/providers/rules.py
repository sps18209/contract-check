"""Deterministic baseline that does not pretend to know the applicable law."""


class RulesProvider:
    name = "rules-v1"

    def propose(self, question: dict, authorities: list[dict]) -> dict:
        return {
            "supporting": "Identify the text and facts supporting the asserted obligation; lawyer analysis required.",
            "opposing": "Test alternative readings, defenses, and limits of the requested remedy; lawyer analysis required.",
            "unknowns": ["Whether the supplied authorities govern these facts and remain good law."],
        }

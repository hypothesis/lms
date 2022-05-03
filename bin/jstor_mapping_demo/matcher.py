import dataclasses
import re
from copy import deepcopy
from dataclasses import dataclass
from typing import List

from lunr import lunr

from bin.jstor_mapping_demo.models import ApplicationInstance, JStorRecord
from bin.jstor_mapping_demo.whois_it import Whois


@dataclass
class Match:
    match_type: str
    jstor_record: JStorRecord
    application_instance: ApplicationInstance
    score: float = None
    matched_on: str = None


class Matcher:
    def __init__(self, jstor_records: List[JStorRecord]):
        self.jstor_records = {record.id: record for record in jstor_records}
        self.text_index = lunr(
            ref="id",
            fields=["summary"],
            documents=[dataclasses.asdict(record) for record in jstor_records],
        )
        self.whois = Whois()

    def match(self, application_instance: ApplicationInstance):
        matches = self._go_for_gold(application_instance)

        if not matches:
            matches = self._text_match(application_instance)

        if not matches:
            expanded_ai = self._lookup_domains(application_instance)
            if expanded_ai:
                matches = self._text_match(expanded_ai)

        return matches or []

    def _go_for_gold(self, application_instance):
        # Try directly looking up the domain against the list of codes. You
        # quite often get a hit, and it's much faster than the text search
        matches = []

        for domain in application_instance.domains:
            jstor_record = self.jstor_records.get(domain)
            if jstor_record:
                matches.append(
                    Match(
                        "domain_match",
                        jstor_record,
                        application_instance,
                        matched_on=domain,
                    )
                )

        return matches

    def _text_match(self, application_instance):
        # Remove things which are interpreted as query string parts
        query = re.sub("[-+:]+", " ", application_instance.summary)
        if not query:
            return None

        text_matches = self.text_index.search(query)
        if not text_matches:
            return None

        return [
            Match(
                "text",
                self.jstor_records[text_match["ref"]],
                application_instance,
                score=text_match["score"],
                matched_on=" ".join(text_matches[0]["match_data"].metadata.keys()),
            )
            for text_match in text_matches
        ]

    def _lookup_domains(self, application_instance):
        expanded_ai = deepcopy(application_instance)

        extra_names = {
            self.whois.get_name(domain) for domain in application_instance.domains
        }
        extra_names.discard(None)
        expanded_ai.names |= extra_names

        if len(expanded_ai.names) - len(application_instance.names):
            return expanded_ai

        return None

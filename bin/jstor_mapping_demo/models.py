import csv
import json
from collections import defaultdict
from dataclasses import dataclass, field

import tldextract


@dataclass
class JStorRecord:
    id: str
    name: str
    summary: str = None

    def __post_init__(self):
        self.summary = f"{self.name} {self.id}"

    @classmethod
    def load(cls, filename):
        with open(filename, encoding="utf-8") as handle:
            return [cls(id=id_, name=name) for id_, name in csv.reader(handle)]


@dataclass
class ApplicationInstance:
    id: int
    names: set = field(default_factory=set)
    domains: set = field(default_factory=set)

    BAD_DOMAIN_LABELS = {
        # Edu software
        "canvas",
        "instructure",
        "hypothesis",
        "brightspace",
        "moodle",
        "blackboard",
        "moodlecloud",
        "sakaiproject",
        "trysakai",
        "sakai",
        # Boring
        "com",
        "www",
        # 3rd party
        "google",
        "gmail",
        "yahoo",
    }

    @property
    def summary(self):
        parts = list(self.names)
        parts.extend(self.domains)
        return " ".join(parts)

    def update(
        self,
        tool_consumer_instance_name,
        lms_url,
        custom_canvas_api_domain,
        email_domain,
        contact_domain,
        **_kwargs,
    ):
        for domain in (email_domain, contact_domain, custom_canvas_api_domain):
            self.add_domain(domain)

        if lms_url:
            ext = tldextract.extract(lms_url, include_psl_private_domains=True)
            self.add_domain(".".join(part for part in ext if part))
            # Add again dropping the minor part, which gets us more hits
            self.add_domain(".".join(part for part in ext[1:] if part))

        if tool_consumer_instance_name:
            self.names.add(tool_consumer_instance_name)

    def add_domain(self, domain):
        if not domain:
            return

        parts = domain.lower().split(".")
        domain = ".".join(
            part.strip() for part in parts if not part in self.BAD_DOMAIN_LABELS
        )
        if not domain:
            return

        self.domains.add(domain)

    @classmethod
    def load(cls, filename):
        with open(filename, encoding="utf-8") as handle:
            application_instances = defaultdict(lambda key: cls(id=key))

            for row in json.load(handle):
                id_ = row["application_instance_id"]
                application_instances.setdefault(id_, cls(id_))
                application_instances[id_].update(**row)

        return list(application_instances.values())

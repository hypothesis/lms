import re
import shelve
import subprocess

from checkmatelib.url import Domain


class Whois:
    _RAW = shelve.open("cache/whois_it.db")

    # This was all generated through a painful manual exercise of running
    # through domains extracted from our data. You'd think:
    #
    #  * There might be some kind of standard to WHOIS records
    #  * That python libraries might be ok at parsing them
    #
    # My experience was that neither is true
    REGEXES = [
        re.compile(r"Registrant.*\bName:\s*(.*?)\n", re.DOTALL | re.IGNORECASE),
        re.compile(
            r"Registrant\n\s*(.*?)\s*$", re.MULTILINE | re.IGNORECASE | re.DOTALL
        ),
        re.compile(
            r"Registrant:\s*(.*?)\s*$", re.MULTILINE | re.IGNORECASE | re.DOTALL
        ),
        re.compile(r"Registered For:\n\s+(.*)\s*$", re.MULTILINE | re.IGNORECASE),
        re.compile(
            r"Registrant ?Organization:\s*(.*)\s*$", re.MULTILINE | re.IGNORECASE
        ),
        re.compile(r"Owner name:\s+(.*?)\s*$", re.MULTILINE | re.IGNORECASE),
        re.compile(r"owner:\s+(.*?)\s*$", re.MULTILINE | re.IGNORECASE),
        re.compile(r"org:\s+(.*?)\s*$", re.MULTILINE | re.IGNORECASE),
        re.compile(r"\[Registrant]\s+(.*?)\s*$", re.MULTILINE | re.IGNORECASE),
        re.compile(r"\[Organization]\s+(.*?)\s*$", re.MULTILINE | re.IGNORECASE),
        re.compile(r"name\.{4,}:\s+(.*?)\s*$", re.MULTILINE | re.IGNORECASE),
    ]

    BAD_NAMES = {
        "exact": {
            "REDACTED FOR PRIVACY",
            "Domain Privacy",
            "DATA REDACTED",
            "Domains By Proxy, LLC",
            "Data Protected",
        },
        "starts": (
            # This happens with blank Org lines above
            "Registrant State/Province:",
            "Contact Privacy Inc",
            "Not shown",
        ),
    }

    BAD_WHOIS = {
        "starts": {
            "NO MATCH",
            "NOT FOUND",
            "No Data Found",
            "El dominio no se encuentra registrado",
            "Requests of this client are not permitted",
            "The queried object does not exist",
        },
        "contains": (
            # These guys give you nothing
            "The DENIC whois service on port 43 doesn't disclose any information",
            "Record maintained by: NL Domain Registry",
            "No match for",
        ),
    }

    def get_name(self, domain):
        raw, domain = self.raw(domain)
        if not raw:
            return None

        if self._matches(raw, **self.BAD_WHOIS):
            return None

        name = self._get_name(raw)

        if not name or self._matches(name, **self.BAD_NAMES):
            return None

        return name

    def raw(self, domain):
        parsed_dom = Domain(domain)
        if not parsed_dom.is_public or parsed_dom.is_ip_v4:
            return None, None

        domain = parsed_dom.root_domain

        if domain not in self._RAW:
            try:
                raw = (
                    subprocess.check_output(["whois", domain], timeout=1)
                    .decode("utf-8")
                    .strip()
                )
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                print(f"Failed to get '{domain}'")
                raw = None

            self._RAW[domain] = raw

        return self._RAW[domain], domain

    def _get_name(self, raw):
        for regex in self.REGEXES:
            match = regex.search(raw)
            if match:
                name = match.group(1)
                if name:
                    return name

        return None

    @staticmethod
    def _matches(string, exact=None, starts=None, contains=None):
        if exact:
            if string in exact:
                return True

        if starts:
            for start in starts:
                if string.startswith(start):
                    return True
        if contains:
            for contain in contains:
                if contain in string:
                    return True

        return False

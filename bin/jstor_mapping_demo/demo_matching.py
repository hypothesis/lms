from collections import Counter

from bin.jstor_mapping_demo.evaluate import evaluate_match
from bin.jstor_mapping_demo.matcher import Matcher
from bin.jstor_mapping_demo.models import ApplicationInstance, JStorRecord

APPLICATION_DATA = "data/application_instances.json"
JSTOR_DATA = "data/jstor.csv"


if __name__ == "__main__":
    matcher = Matcher(jstor_records=JStorRecord.load(JSTOR_DATA))
    application_instances = ApplicationInstance.load(APPLICATION_DATA)

    outcomes = Counter()

    for pos, application_instance in enumerate(application_instances):
        print(f"Match ({pos + 1}/{len(application_instances)})", application_instance)
        print(f"\t| {application_instance.summary}")
        matches = matcher.match(application_instance)

        print(f"\tGot {len(matches)} match(es):")
        for match in matches[:5]:
            evaluation = evaluate_match(match)
            print(f"\t * [{evaluation}]: {match}")
            print(f"\t\t| {match.jstor_record.summary}")
            print(f"\t\t| Matched on: {match.matched_on}")

        if matches:
            outcomes[evaluate_match(matches[0])] += 1
        else:
            outcomes["fail"] += 1

    print("\nResults:")
    print(outcomes)

from collections import Counter
from functools import lru_cache
import re

from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig
import spacy

ENTITIES = ["PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER", "CREDIT_CARD", "US_SSN", "IP_ADDRESS", "IBAN_CODE"]
ENTITY_KEYS = {"EMAIL_ADDRESS": "email", "PHONE_NUMBER": "phone"}


@lru_cache(maxsize=1)
def analyzer():
    if not spacy.util.is_package("en_core_web_md"):
        raise ValueError("The English NLP model is missing. Install the project's pinned requirements before using Presidio mode.")
    provider = NlpEngineProvider(
        nlp_configuration={"nlp_engine_name": "spacy", "models": [{"lang_code": "en", "model_name": "en_core_web_md"}]}
    )
    engine = provider.create_engine()
    engine.nlp["en"].max_length = 2_000_001
    return AnalyzerEngine(nlp_engine=engine, supported_languages=["en"])


def redact_pii(text):
    engine = analyzer()
    artifacts = engine.nlp_engine.process_text(text, "en")
    detections = engine.analyze(text=text, language="en", entities=ENTITIES, score_threshold=0.5, nlp_artifacts=artifacts)
    selected = []
    for detection in sorted(detections, key=lambda span: (-span.score, span.start, -span.end)):
        if detection.entity_type == "PERSON":
            phrase = text[detection.start : detection.end]
            name_words = re.findall(r"[^\W\d_]+(?:['-][^\W\d_]+)*", phrase)
            name_tokens = [token for token in artifacts.tokens if detection.start <= token.idx < detection.end and token.is_alpha]
            if any(character.isdigit() for character in phrase) or len(name_words) < 2 or not all(word[0].isupper() for word in name_words) or len(name_tokens) < 2 or not all(token.pos_ == "PROPN" for token in name_tokens):
                continue
        if not any(detection.start < previous.end and previous.start < detection.end for previous in selected):
            selected.append(detection)
    operators = {entity: OperatorConfig("replace", {"new_value": f"[{entity}]"}) for entity in ENTITIES}
    redacted = AnonymizerEngine().anonymize(text=text, analyzer_results=selected, operators=operators)
    counts = Counter(ENTITY_KEYS.get(span.entity_type, span.entity_type.lower()) for span in selected)
    return redacted.text, dict(counts)

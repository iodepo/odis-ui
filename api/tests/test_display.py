from app.search.display import display_for
from app.search.gleaner.queries import map_document_to_item


MARCO_BOLO_PERSON = {
    "source": "marco-bolo-dataset-catalogue",
    "id": "https://w3id.org/marco-bolo/mbo_fbd9101a-77af-46a2-8573-1e7a17caeb9d",
    "type": ["Person"],
    "name": None,
    "description": None,
    "url": None,
    "source_url": (
        "https://lab.marcobolo-project.eu/csv-to-json-ld/schema-jsonld/"
        "mbo_fbd9101a-77af-46a2-8573-1e7a17caeb9d.json"
    ),
    "jsonld": {
        "@type": "Person",
        "affiliation": {
            "@type": "ResearchProject",
            "name": "MARCO-BOLO Work Package 2",
        },
        "familyName": "Warwick-Dugdale",
        "givenName": "Joanna",
        "identifier": [
            "https://oceanexpert.org/expert/88666",
            "https://orcid.org/0000-0001-5242-6706",
        ],
        "worksFor": {
            "@type": "GovernmentOrganization",
            "legalName": "Marine Biological Association Of The United Kingdom",
            "name": "MBA",
        },
    },
}


def test_person_title_falls_back_to_given_and_family_name() -> None:
    item = map_document_to_item(
        MARCO_BOLO_PERSON["id"],
        MARCO_BOLO_PERSON,
    )
    assert item.title == "Joanna Warwick-Dugdale"
    labels = {fact.label: fact for fact in item.facts}
    assert labels["Organization"].value == (
        "Marine Biological Association Of The United Kingdom"
    )
    assert labels["Affiliation"].value == "MARCO-BOLO Work Package 2"
    assert labels["ORCID"].value == "0000-0001-5242-6706"
    assert labels["ORCID"].href == "https://orcid.org/0000-0001-5242-6706"
    assert labels["OceanExpert"].href == "https://oceanexpert.org/expert/88666"


def test_person_title_prefers_name_over_given_family() -> None:
    display = display_for(
        {
            "type": ["Person"],
            "name": "Ada Lovelace",
            "jsonld": {"givenName": "Augusta", "familyName": "Lovelace"},
        },
        "person",
    )
    assert display.title == "Ada Lovelace"


def test_person_title_from_schema_prefixed_jsonld() -> None:
    display = display_for(
        {
            "type": ["Person"],
            "name": None,
            "jsonld": {
                "schema:givenName": "Joanna",
                "schema:familyName": "Warwick-Dugdale",
            },
        },
        "person",
    )
    assert display.title == "Joanna Warwick-Dugdale"


def test_person_title_given_name_only() -> None:
    display = display_for(
        {"type": ["Person"], "jsonld": {"givenName": "Joanna"}},
        "person",
    )
    assert display.title == "Joanna"


def test_dataset_untitled_without_name() -> None:
    display = display_for({"type": ["Dataset"], "name": None}, "dataset")
    assert display.title == "(untitled)"
    assert display.facts == ()


def test_organization_title_falls_back_to_legal_name() -> None:
    display = display_for(
        {
            "type": ["Organization"],
            "name": None,
            "jsonld": {"legalName": "Marine Biological Association"},
        },
        "organization",
    )
    assert display.title == "Marine Biological Association"

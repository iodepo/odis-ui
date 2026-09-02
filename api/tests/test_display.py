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


def test_dataset_facts_license_and_temporal_coverage() -> None:
    display = display_for(
        {
            "type": ["Dataset"],
            "name": "Storm events",
            "jsonld": {
                "license": "https://creativecommons.org/publicdomain/zero/1.0/",
                "temporalCoverage": "1950-01-01/2013-12-18",
            },
        },
        "dataset",
    )
    labels = {fact.label: fact for fact in display.facts}
    assert labels["License"].value == "CC0 1.0"
    assert labels["License"].href == "https://creativecommons.org/publicdomain/zero/1.0/"
    assert labels["Temporal coverage"].value == "1950-01-01/2013-12-18"


def test_dataset_license_from_resolved_creative_work() -> None:
    display = display_for(
        {
            "type": ["Dataset"],
            "name": "eDNA sequences",
            "jsonld": {
                "license": {
                    "@type": "CreativeWork",
                    "name": "CC-BY-4.0",
                    "schema:url": {
                        "@type": "URL",
                        "@value": "https://spdx.org/licenses/CC-BY-4.0",
                    },
                },
                "temporalCoverage": "2021-08-17/2024-08-29",
            },
        },
        "dataset",
    )
    labels = {fact.label: fact for fact in display.facts}
    assert labels["License"].value == "CC-BY-4.0"
    assert labels["License"].href == "https://spdx.org/licenses/CC-BY-4.0"
    assert labels["Temporal coverage"].value == "2021-08-17/2024-08-29"


def test_dataset_temporal_coverage_open_ended() -> None:
    display = display_for(
        {
            "type": ["Dataset"],
            "name": "Ongoing survey",
            "jsonld": {"temporalCoverage": "2015-11/.."},
        },
        "dataset",
    )
    labels = {fact.label: fact for fact in display.facts}
    assert labels["Temporal coverage"].value == "2015-11 – present"


def test_dataset_unresolved_license_reference_is_omitted() -> None:
    display = display_for(
        {
            "type": ["Dataset"],
            "name": "Partial metadata",
            "jsonld": {
                "license": "https://w3id.org/marco-bolo/mbo_500ee36e-324d-4f2f-9b0b-a4408f638201",
                "temporalCoverage": "2000/2023",
            },
        },
        "dataset",
    )
    labels = {fact.label: fact for fact in display.facts}
    assert "License" not in labels
    assert labels["Temporal coverage"].value == "2000/2023"


def test_dataset_facts_via_map_document_to_item() -> None:
    item = map_document_to_item(
        "https://example.org/dataset/1",
        {
            "source": "medin",
            "type": ["Dataset"],
            "name": "Lundy fauna",
            "jsonld": {
                "license": "https://spdx.org/licenses/CC-BY-4.0",
                "temporalCoverage": "1848/1975",
            },
        },
    )
    labels = {fact.label: fact for fact in item.facts}
    assert item.title == "Lundy fauna"
    assert labels["License"].value == "CC-BY-4.0"
    assert labels["Temporal coverage"].value == "1848/1975"


def test_publication_lists_single_author() -> None:
    display = display_for(
        {
            "type": ["CreativeWork"],
            "name": "Ocean acidification review",
            "jsonld": {
                "author": {"@type": "Person", "name": "Jane Doe"},
            },
        },
        "creativework",
    )
    labels = {fact.label: fact for fact in display.facts}
    assert labels["Author"].value == "Jane Doe"


def test_publication_lists_multiple_authors() -> None:
    display = display_for(
        {
            "type": ["CreativeWork"],
            "name": "Coastal monitoring report",
            "jsonld": {
                "author": [
                    {"@type": "Person", "givenName": "Joanna", "familyName": "Smith"},
                    {"@type": "Person", "name": "Ada Lovelace"},
                ],
            },
        },
        "creativework",
    )
    labels = {fact.label: fact for fact in display.facts}
    assert labels["Authors"].value == "Joanna Smith, Ada Lovelace"


def test_publication_author_falls_back_to_creator() -> None:
    display = display_for(
        {
            "type": ["ScholarlyArticle"],
            "name": "Phytoplankton trends",
            "jsonld": {
                "creator": {"@type": "Organization", "name": "VLIZ"},
            },
        },
        "scholarlyarticle",
    )
    labels = {fact.label: fact for fact in display.facts}
    assert labels["Author"].value == "VLIZ"


def test_publication_deduplicates_author_and_creator() -> None:
    display = display_for(
        {
            "type": ["CreativeWork"],
            "name": "Duplicate authorship",
            "jsonld": {
                "author": {"@type": "Person", "name": "Jane Doe"},
                "creator": {"@type": "Person", "name": "Jane Doe"},
            },
        },
        "creativework",
    )
    labels = {fact.label: fact for fact in display.facts}
    assert labels["Author"].value == "Jane Doe"


def test_publication_unresolved_author_reference_is_omitted() -> None:
    display = display_for(
        {
            "type": ["CreativeWork"],
            "name": "Draft paper",
            "jsonld": {
                "author": {"@id": "https://w3id.org/marco-bolo/mbo_bf08f5c2-fef3-48a1-80b3-413534d2925b"},
            },
        },
        "creativework",
    )
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

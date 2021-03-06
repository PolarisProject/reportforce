import pytest

from reportforce import Reportforce
from fixtures_utils import read_json

REPORT = read_json("tabular.json")
METADATA = read_json("tabular_metadata.json")


@pytest.fixture
def setup(mock_login, mock_http_request, mock_get_metadata):
    """Simulate getting a report with these parameters.

    We expected the underlying report metadata dictionary
    to change accordingly.
    """
    mock_http_request(REPORT, "post")
    mock_get_metadata(METADATA)

    rf = Reportforce("foo@bar.com", "1234", "XXX")
    rf.get_report(
        "ID",
        filters=[("Opportunity Name", "!=", "VALUE")],
        logic="1 AND 2",
        id_column="Opportunity Name",
        start="01-01-2020",
        end="2020-01-31",
        date_column="Fiscal Period",
    )

    return rf


def test_logic(setup):
    logic = setup.metadata["reportMetadata"]["reportBooleanFilter"]
    expected_logic = "1 AND 2 AND 3"

    assert logic == expected_logic


def test_date_filter(setup):
    dates = setup.metadata["reportMetadata"]["standardDateFilter"]
    expected_dates = {
        "column": "FISCAL_QUARTER",
        "durationValue": "CUSTOM",
        "startDate": "2020-01-01",
        "endDate": "2020-01-31",
    }

    assert dates == expected_dates


def test_report_filters(setup):
    filters = setup.metadata["reportMetadata"]["reportFilters"]
    expected_filters = [
        {
            "column": "column",
            "filterType": "filterType",
            "isRunPageEditable": True,
            "operator": "operator",
            "value": "value",
        },
        {"column": "OPPORTUNITY_NAME", "operator": "notEqual", "value": "VALUE"},
        {
            "column": "OPPORTUNITY_NAME",
            "operator": "notEqual",
            "value": "Acme - 200 Widgets",
        },
    ]

    assert filters == expected_filters

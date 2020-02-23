import pandas as pd

from .. import helpers

base_url = "https://{}/services/data/v{}/analytics/reports/{}"


def report_generator(get_report):
    dtypes = {}
    """
    Decorator function to generate reports until the allData element of the
    response body is 'true', while filtering out already seen values of
    a specified column, namely the id_column.

    Once all data has been collected, it concatenates them all and tries to
    convert the columns dtypes accordingly.
    """

    def generator(report_id, id_column, metadata, session):
        """Request reports until allData is true by filtering them iteratively."""
        url = base_url.format(session.instance_url, session.version, report_id)

        report, report_cells, indices = get_report(url, metadata, session)

        columns = helpers.parsers.get_columns(report)

        nonlocal dtypes
        dtypes = helpers.parsers.get_columns_types(report)

        df = pd.DataFrame(report_cells, index=indices, columns=columns)
        yield df

        if id_column:
            already_seen = ""
            helpers.filtering.set_filters([(id_column, "!=", already_seen)], metadata)
            helpers.filtering.increment_logical_filter(metadata)

            while not report["allData"]:
                # getting what is needed to build the dataframe
                report, report_cells, indices = get_report(url, metadata, session)

                # filtering out already seen values
                if id_column:
                    already_seen += ",".join(df[id_column].values)
                    helpers.filtering.update_filter(-1, "value", already_seen, metadata)

                df = pd.DataFrame(report_cells, index=indices, columns=columns)
                yield df

    def concat(*args, **kwargs):
        """Concantenate reports and convert columns dtypes."""
        df = pd.concat(generator(*args, **kwargs))

        for col, dtype in zip(df, dtypes):
            if dtype == "percent":
                df[col] = pd.to_numeric(df[col].str.rstrip("%")) / 100
            elif dtype == "currency":
                df[col] = pd.to_numeric(df[col].str.replace("[^.0-9]", ""))
            elif dtype.startswith("date"):
                df[col] = pd.to_datetime(df[col])
            elif dtype != "object":
                df[col] = df[col].astype(dtype)


        return df

    return concat

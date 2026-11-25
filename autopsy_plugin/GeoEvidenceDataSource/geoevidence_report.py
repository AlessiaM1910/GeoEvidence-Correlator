"""HTML reports generated from the GeoEvidence results saved in the case."""

import io
import os
import time

from org.sleuthkit.datamodel import BlackboardAttribute

from geoevidence_common import MODULE_VERSION, UNKNOWN_DATE


SUMMARY_STATUSES = [
    ("INSIDE_RADIUS", u"Inside the search area"),
    ("OUTSIDE_RADIUS", u"Outside the search area"),
    ("NO_GPS", u"No GPS position"),
    ("INVALID_GPS", u"Invalid or incomplete GPS"),
    ("UNREADABLE", u"Unreadable files"),
    ("SKIPPED_NO_EXIFTOOL", u"Videos skipped (ExifTool not found)"),
]

REPORT_STYLE = u"""
body { font-family: Arial, sans-serif; margin: 2em; color: #222; }
h1 { color: #0b5d8a; }
h2 { color: #0b5d8a; border-bottom: 1px solid #ccc; padding-bottom: 0.2em; }
table { border-collapse: collapse; margin: 0.5em 0 1.5em 0; }
th, td { border: 1px solid #ccc; padding: 4px 10px; text-align: left; }
th { background: #eee; }
"""


def html_escape(value):
    """Protect the characters that have a special meaning in HTML."""
    text = u"%s" % value
    text = text.replace(u"&", u"&amp;")
    text = text.replace(u"<", u"&lt;")
    text = text.replace(u">", u"&gt;")
    text = text.replace(u'"', u"&quot;")
    return text


def format_number(value, decimals):
    if value is None:
        return u""
    return u"%.*f" % (decimals, value)


def attribute_text(artifact, attribute_type):
    attribute = artifact.getAttribute(attribute_type)
    if attribute is None:
        return u""
    return attribute.getValueString()


def attribute_number(artifact, attribute_type):
    attribute = artifact.getAttribute(attribute_type)
    if attribute is None:
        return None
    return attribute.getValueDouble()


def table_html(headers, body_rows):
    '''Creates a table'''
    parts = [u"<table>"]
    parts.append(
        u"<tr>"
        + u"".join(u"<th>%s</th>" % html_escape(h) for h in headers)
        + u"</tr>"
    )
    for cells in body_rows:
        parts.append(
            u"<tr>"
            + u"".join(u"<td>%s</td>" % html_escape(c) for c in cells)
            + u"</tr>"
        )
    parts.append(u"</table>")
    return u"\n".join(parts)

def read_result_rows(case, data_source, blackboard, types, parameters):
    """Read the saved results of this data source for one set of parameters."""
    rows = []
    artifacts = blackboard.getDataArtifacts(
        types["artifact"].getTypeID(), data_source.getId()
    )

    for artifact in artifacts:
        if attribute_text(artifact, types["parameters"]) != parameters:
            continue

        source_file = case.getSleuthkitCase().getAbstractFileById(
            artifact.getObjectID()
        )
        name = u""
        path = u""
        if source_file is not None:
            name = source_file.getName()
            path = source_file.getParentPath() + source_file.getName()

        rows.append({
            "status": attribute_text(artifact, types["status"]),
            "source": attribute_text(artifact, types["source"]),
            "media_type": attribute_text(artifact, types["media_type"]),
            "timestamp": attribute_text(artifact, types["timestamp"]),
            "distance_km": attribute_number(artifact, types["distance_km"]),
            "latitude": attribute_number(
                artifact, BlackboardAttribute.Type.TSK_GEO_LATITUDE
            ),
            "longitude": attribute_number(
                artifact, BlackboardAttribute.Type.TSK_GEO_LONGITUDE
            ),
            "name": name,
            "path": path,
        })

    return rows

def write_summary_report(report_path, info, rows):
    counts = {}
    for row in rows:
        counts[row["status"]] = counts.get(row["status"], 0) + 1

    inside = [row for row in rows if row["status"] == "INSIDE_RADIUS"]
    inside.sort(key=lambda row: (
        row["timestamp"] == UNKNOWN_DATE,
        row["timestamp"],
        row["name"].lower(),
    ))

    summary_rows = [[u"Files analyzed", len(rows)]]
    for code, label in SUMMARY_STATUSES:
        summary_rows.append([label, counts.get(code, 0)])

    parts = [
        u"<!DOCTYPE html>",
        u'<html><head><meta charset="utf-8">',
        u"<title>GeoEvidence summary report</title>",
        u"<style>%s</style></head><body>" % REPORT_STYLE,
        u"<h1>GeoEvidence - Summary report</h1>",
        table_html(
            [u"Case", u"Data source", u"Generated", u"Module version"],
            [[info["case_name"], info["data_source"],
              info["generated"], info["version"]]],
        ),
        u"<h2>Search parameters</h2>",
        table_html(
            [u"Center latitude", u"Center longitude", u"Radius"],
            [[u"%.6f" % info["center_lat"],
              u"%.6f" % info["center_lon"],
              u"%g km" % info["radius_km"]]],
        ),
        u"<h2>Summary</h2>",
        table_html([u"Outcome", u"Files"], summary_rows),
        u"<h2>Evidence inside the search area</h2>",
    ]

    if inside:
        body = []
        for number, row in enumerate(inside, 1):
            body.append([
                number,
                row["name"],
                row["media_type"],
                row["timestamp"],
                format_number(row["latitude"], 6),
                format_number(row["longitude"], 6),
                format_number(row["distance_km"], 3),
            ])
        parts.append(table_html(
            [u"#", u"File", u"Type", u"Metadata date",
             u"Latitude", u"Longitude", u"Distance (km)"],
            body,
        ))
    else:
        parts.append(u"<p>No evidence inside the search area.</p>")

    parts.append(u"</body></html>")

    handle = io.open(report_path, "w", encoding="utf-8")
    try:
        handle.write(u"\n".join(parts))
    finally:
        handle.close()


def save_summary_report(case, data_source, blackboard, types,
                        parameters, center, radius_km):
    """Write the summary report in the Reports folder of the case."""
    rows = read_result_rows(case, data_source, blackboard, types, parameters)

    report_directory = case.getReportDirectory()
    if not os.path.exists(report_directory):
        os.makedirs(report_directory)

    report_path = os.path.join(
        report_directory,
        "GeoEvidence_summary_%s.html" % time.strftime("%Y%m%d_%H%M%S"),
    )

    info = {
        "case_name": case.getDisplayName(),
        "data_source": data_source.getName(),
        "generated": time.strftime("%Y/%m/%d %H:%M:%S"),
        "version": MODULE_VERSION,
        "center_lat": center.lat,
        "center_lon": center.lon,
        "radius_km": radius_km,
    }

    write_summary_report(report_path, info, rows)
    return report_path

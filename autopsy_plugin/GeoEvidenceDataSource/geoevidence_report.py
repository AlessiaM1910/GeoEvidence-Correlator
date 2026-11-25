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

def list_runs(case, blackboard, types):
    """Return the saved runs of the case, the most recent first."""
    runs = {}

    for data_source in case.getSleuthkitCase().getDataSources():
        artifacts = blackboard.getDataArtifacts(
            types["artifact"].getTypeID(), data_source.getId()
        )
        for artifact in artifacts:
            parameters = attribute_text(artifact, types["parameters"])
            key = (data_source.getId(), parameters)
            artifact_id = artifact.getArtifactID()

            run = runs.get(key)
            if run is None:
                run = {
                    "data_source": data_source,
                    "parameters": parameters,
                    "center_lat": attribute_number(
                        artifact, types["center_lat"]
                    ),
                    "center_lon": attribute_number(
                        artifact, types["center_lon"]
                    ),
                    "radius_km": attribute_number(
                        artifact, types["radius_km"]
                    ),
                    "latest_id": artifact_id,
                    "files": 0,
                }
                runs[key] = run

            run["files"] += 1
            if artifact_id > run["latest_id"]:
                run["latest_id"] = artifact_id

    ordered = list(runs.values())
    ordered.sort(key=lambda run: run["latest_id"], reverse=True)
    return ordered


STATUS_REASONS = {
    "NO_GPS": u"The file has no GPS position in its metadata.",
    "INVALID_GPS": u"The GPS data is incomplete or outside the valid range.",
    "UNREADABLE": u"The file could not be read (corrupt or unsupported).",
    "SKIPPED_NO_EXIFTOOL": u"Video skipped: ExifTool was not available.",
}

REPORT_NOTES = [
    u"The date is the one written in the file metadata (EXIF for photos, "
    u"the container for videos). It can be missing, wrong or altered, and "
    u"it is not the date of the file system.",
    u"Dates without a time zone are shown as written and are not converted.",
    u"The coordinates are those declared by the device in the metadata, "
    u"with the precision of the device.",
    u"A file is inside the area when its distance from the center is less "
    u"than or equal to the radius.",
    u"Distances are computed on a sphere (Haversine formula, Earth radius "
    u"6371 km); the error is up to about 0.5% compared with an ellipsoid.",
    u"Only JPEG and MP4/MOV files are analyzed. Other formats, for example "
    u"HEIC, are not included.",
]


def count_statuses(rows):
    counts = {}
    for row in rows:
        counts[row["status"]] = counts.get(row["status"], 0) + 1
    return counts


def date_sort_key(row):
    """Order by metadata date; unknown dates go last."""
    return (
        row["timestamp"] == UNKNOWN_DATE,
        row["timestamp"],
        row["name"].lower(),
    )

LOCATED_HEADERS = [
    u"#", u"File", u"Path", u"Type", u"Source",
    u"Metadata date", u"Latitude", u"Longitude", u"Distance (km)",
]


def heading(text, level):
    return u"<%s>%s</%s>" % (level, html_escape(text), level)


def build_case_info(case):
    return {
        "case_name": case.getDisplayName(),
        "generated": time.strftime("%Y/%m/%d %H:%M:%S"),
        "version": MODULE_VERSION,
    }


def collect_runs_data(case, blackboard, types):
    """Return [(info, rows), ...] for every run of the case, oldest first."""
    runs = list_runs(case, blackboard, types)
    runs.reverse()

    runs_data = []
    for run in runs:
        rows = read_result_rows(
            case, run["data_source"], blackboard, types, run["parameters"]
        )
        info = {
            "data_source": run["data_source"].getName(),
            "center_lat": run["center_lat"],
            "center_lon": run["center_lon"],
            "radius_km": run["radius_km"],
        }
        runs_data.append((info, rows))

    return runs_data


def parameters_table(info):
    return table_html(
        [u"Data source", u"Center latitude", u"Center longitude", u"Radius"],
        [[info["data_source"],
          u"%.6f" % info["center_lat"],
          u"%.6f" % info["center_lon"],
          u"%g km" % info["radius_km"]]],
    )


def summary_table(rows):
    counts = count_statuses(rows)
    body = [[u"Files analyzed", len(rows)]]
    for code, label in SUMMARY_STATUSES:
        body.append([label, counts.get(code, 0)])
    return table_html([u"Outcome", u"Files"], body)


def located_rows(selected):
    body = []
    for number, row in enumerate(selected, 1):
        body.append([
            number, row["name"], row["path"], row["media_type"],
            row["source"], row["timestamp"],
            format_number(row["latitude"], 6),
            format_number(row["longitude"], 6),
            format_number(row["distance_km"], 3),
        ])
    return body


def runs_overview(runs_data):
    body = []
    for number, (info, rows) in enumerate(runs_data, 1):
        counts = count_statuses(rows)
        body.append([
            number,
            info["data_source"],
            u"%.6f, %.6f" % (info["center_lat"], info["center_lon"]),
            u"%g km" % info["radius_km"],
            len(rows),
            counts.get("INSIDE_RADIUS", 0),
            counts.get("OUTSIDE_RADIUS", 0),
        ])
    return table_html(
        [u"Run", u"Data source", u"Center", u"Radius",
         u"Files", u"Inside", u"Outside"],
        body,
    )


def summary_section(info, rows, level):
    """Sections of the summary report for one run."""
    inside = [row for row in rows if row["status"] == "INSIDE_RADIUS"]
    inside.sort(key=date_sort_key)

    parts = [
        heading(u"Search parameters", level),
        parameters_table(info),
        heading(u"Summary", level),
        summary_table(rows),
        heading(u"Evidence inside the search area", level),
    ]

    if inside:
        body = []
        for number, row in enumerate(inside, 1):
            body.append([
                number, row["name"], row["media_type"], row["timestamp"],
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

    return parts


def verbose_section(info, rows, level):
    """Sections of the verbose report for one run."""
    inside = [row for row in rows if row["status"] == "INSIDE_RADIUS"]
    inside.sort(key=date_sort_key)

    outside = [row for row in rows if row["status"] == "OUTSIDE_RADIUS"]
    outside.sort(key=lambda row: (row["distance_km"], row["name"].lower()))

    not_evaluated = [
        row for row in rows
        if row["status"] not in ("INSIDE_RADIUS", "OUTSIDE_RADIUS")
    ]
    not_evaluated.sort(key=lambda row: (row["status"], row["name"].lower()))

    parts = [
        heading(u"Search parameters", level),
        parameters_table(info),
        heading(u"Summary", level),
        summary_table(rows),
        heading(u"Evidence inside the search area", level),
    ]

    if inside:
        parts.append(table_html(LOCATED_HEADERS, located_rows(inside)))
    else:
        parts.append(u"<p>No evidence inside the search area.</p>")

    parts.append(heading(u"Evidence outside the search area", level))
    if outside:
        parts.append(table_html(LOCATED_HEADERS, located_rows(outside)))
    else:
        parts.append(u"<p>No evidence outside the search area.</p>")

    parts.append(heading(u"Files that could not be evaluated", level))
    if not_evaluated:
        body = []
        for number, row in enumerate(not_evaluated, 1):
            body.append([
                number, row["name"], row["path"], row["media_type"],
                row["status"], STATUS_REASONS.get(row["status"], u""),
                row["timestamp"],
            ])
        parts.append(table_html(
            [u"#", u"File", u"Path", u"Type", u"Outcome", u"Reason",
             u"Metadata date"],
            body,
        ))
    else:
        parts.append(u"<p>All the files could be evaluated.</p>")

    return parts


def write_html_report(report_path, title, case_info, runs_data,
                      build_section, intro_parts, closing_parts):
    """One HTML file with a section for every run of the case."""
    many_runs = len(runs_data) > 1

    parts = [
        u"<!DOCTYPE html>",
        u'<html><head><meta charset="utf-8">',
        u"<title>%s</title>" % html_escape(title),
        u"<style>%s</style></head><body>" % REPORT_STYLE,
        u"<h1>%s</h1>" % html_escape(title),
        table_html(
            [u"Case", u"Generated", u"Module version"],
            [[case_info["case_name"], case_info["generated"],
              case_info["version"]]],
        ),
    ]
    parts.extend(intro_parts)

    if many_runs:
        parts.append(heading(u"Runs in this case", u"h2"))
        parts.append(runs_overview(runs_data))

    for number, (info, rows) in enumerate(runs_data, 1):
        if many_runs:
            parts.append(heading(
                u"Run %d: center %.6f, %.6f, radius %g km" % (
                    number, info["center_lat"], info["center_lon"],
                    info["radius_km"]),
                u"h2",
            ))
            parts.extend(build_section(info, rows, u"h3"))
        else:
            parts.extend(build_section(info, rows, u"h2"))

    parts.extend(closing_parts)
    parts.append(u"</body></html>")

    handle = io.open(report_path, "w", encoding="utf-8")
    try:
        handle.write(u"\n".join(parts))
    finally:
        handle.close()


def make_report_path(case, report_directory, file_name):
    if report_directory is None:
        report_directory = case.getReportDirectory()
    if not os.path.exists(report_directory):
        os.makedirs(report_directory)
    return os.path.join(report_directory, file_name)


def save_summary_report(case, blackboard, types,
                        report_directory=None,
                        file_name="GeoEvidence_summary.html"):
    """Write the summary report. Return its path, or None if no results."""
    runs_data = collect_runs_data(case, blackboard, types)
    if not runs_data:
        return None

    report_path = make_report_path(case, report_directory, file_name)
    write_html_report(
        report_path, u"GeoEvidence - Summary report",
        build_case_info(case), runs_data, summary_section, [], [],
    )
    return report_path


def save_verbose_report(case, blackboard, types,
                        report_directory=None,
                        file_name="GeoEvidence_verbose.html"):
    """Write the verbose report. Return its path, or None if no results."""
    runs_data = collect_runs_data(case, blackboard, types)
    if not runs_data:
        return None

    intro = [
        heading(u"Method", u"h2"),
        u"<p>Photos are read with the metadata-extractor library bundled "
        u"with Autopsy. Videos are exported to a temporary copy and read "
        u"with ExifTool. The distance of each file from the center of the "
        u"search area is compared with the radius.</p>",
    ]
    closing = [
        heading(u"Notes and limits", u"h2"),
        u"<ul>"
        + u"".join(u"<li>%s</li>" % html_escape(n) for n in REPORT_NOTES)
        + u"</ul>",
    ]

    report_path = make_report_path(case, report_directory, file_name)
    write_html_report(
        report_path, u"GeoEvidence - Verbose report",
        build_case_info(case), runs_data, verbose_section, intro, closing,
    )
    return report_path
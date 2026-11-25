"""Custom result type of GeoEvidence: one result for every analyzed file."""

from java.util import ArrayList

from org.sleuthkit.datamodel import BlackboardArtifact
from org.sleuthkit.datamodel import BlackboardAttribute

from geoevidence_common import MODULE_NAME, RESULT_ARTIFACT_NAME

def register_result_types(blackboard):
    """Create (or fetch) the custom result type and its attribute types."""
    value_type = BlackboardAttribute.TSK_BLACKBOARD_ATTRIBUTE_VALUE_TYPE

    definitions = [
        ("status", "GEOEVIDENCE_STATUS", value_type.STRING, "Status"),
        ("source", "GEOEVIDENCE_SOURCE", value_type.STRING, "Source"),
        ("parameters", "GEOEVIDENCE_PARAMETERS", value_type.STRING,
         "Search parameters"),
        ("media_type", "GEOEVIDENCE_MEDIA_TYPE", value_type.STRING,
         "Media type"),
        ("timestamp", "GEOEVIDENCE_TIMESTAMP", value_type.STRING,
         "Metadata date"),
        ("distance_km", "GEOEVIDENCE_DISTANCE_KM", value_type.DOUBLE,
         "Distance (km)"),
        ("center_lat", "GEOEVIDENCE_CENTER_LAT", value_type.DOUBLE,
         "Center latitude"),
        ("center_lon", "GEOEVIDENCE_CENTER_LON", value_type.DOUBLE,
         "Center longitude"),
        ("radius_km", "GEOEVIDENCE_RADIUS_KM", value_type.DOUBLE,
         "Radius (km)"),
    ]

    types = {}
    for key, type_name, kind, display_name in definitions:
        types[key] = blackboard.getOrAddAttributeType(
            type_name, kind, display_name
        )

    types["artifact"] = blackboard.getOrAddArtifactType(
        RESULT_ARTIFACT_NAME,
        "GeoEvidence Result",
        BlackboardArtifact.Category.DATA_ARTIFACT,
    )

    return types


def post_result(blackboard, source_file, types, row):
    """Save one result for a file. Return True if it was created."""
    artifact_type = types["artifact"]

    # Identity of a result: file, outcome, source and search parameters.
    key_attributes = ArrayList()
    for key in ("status", "source", "parameters"):
        key_attributes.add(
            BlackboardAttribute(types[key], MODULE_NAME, row[key])
        )

    if blackboard.artifactExists(source_file, artifact_type, key_attributes):
        return False

    attributes = ArrayList()
    attributes.addAll(key_attributes)

    for key in ("media_type", "timestamp"):
        attributes.add(
            BlackboardAttribute(types[key], MODULE_NAME, row[key])
        )

    for key in ("center_lat", "center_lon", "radius_km"):
        attributes.add(
            BlackboardAttribute(types[key], MODULE_NAME, float(row[key]))
        )

    if row["distance_km"] is not None:
        attributes.add(
            BlackboardAttribute(
                types["distance_km"],
                MODULE_NAME,
                float(round(row["distance_km"], 3)),
            )
        )

    if row["latitude"] is not None and row["longitude"] is not None:
        attributes.add(
            BlackboardAttribute(
                BlackboardAttribute.Type.TSK_GEO_LATITUDE,
                MODULE_NAME,
                float(row["latitude"]),
            )
        )
        attributes.add(
            BlackboardAttribute(
                BlackboardAttribute.Type.TSK_GEO_LONGITUDE,
                MODULE_NAME,
                float(row["longitude"]),
            )
        )

    result = source_file.newDataArtifact(artifact_type, attributes)
    blackboard.postArtifact(result, MODULE_NAME)
    return True

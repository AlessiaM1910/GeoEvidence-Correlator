"""First Data Source Ingest Module for GeoEvidence.

This checkpoint only discovers supported media and reports their count. This checkpoint counts supported media and reads existing EXIF coordinate
results produced by Picture Analyzer. It does not yet invoke ExifTool or
create GeoEvidence Blackboard artifacts.
"""

import inspect
from java.util import ArrayList

from georange import Coordinate
from org.sleuthkit.datamodel import Score
from java.util.logging import Level

from org.sleuthkit.autopsy.casemodule import Case
from org.sleuthkit.autopsy.coreutils import Logger
from org.sleuthkit.autopsy.ingest import DataSourceIngestModule
from org.sleuthkit.autopsy.ingest import IngestMessage
from org.sleuthkit.autopsy.ingest import IngestModule
from org.sleuthkit.autopsy.ingest import IngestModuleFactoryAdapter
from org.sleuthkit.autopsy.ingest import IngestServices
from org.sleuthkit.datamodel import BlackboardArtifact
from org.sleuthkit.datamodel import BlackboardAttribute
from java.lang import Throwable
from org.sleuthkit.datamodel import ReadContentInputStream
from com.drew.imaging import ImageMetadataReader
from com.drew.metadata.exif import GpsDirectory


MODULE_NAME = "GeoEvidence Data Source"

# JPEG and MP4/MOV are the validated first scope of the project.
SUPPORTED_EXTENSIONS = (".jpg", ".jpeg", ".mp4", ".mov")
CENTER_LATITUDE = 39.375155
CENTER_LONGITUDE = 16.271693
RADIUS_KM = 1.0
PHOTO_EXTENSIONS = (".jpg", ".jpeg")

VALID_GPS = "VALID_GPS"
NO_GPS = "NO_GPS"
INVALID_GPS = "INVALID_GPS"
UNREADABLE = "UNREADABLE"


def read_photo_gps(abstract_file):
    """Return (status, latitude, longitude) for one photo."""
    try:
        stream = ReadContentInputStream(abstract_file)
        try:
            metadata = ImageMetadataReader.readMetadata(stream)
        finally:
            stream.close()

        gps = metadata.getFirstDirectoryOfType(GpsDirectory)
        if gps is None:
            return NO_GPS, None, None

        location = gps.getGeoLocation()
        if location is None:
            return INVALID_GPS, None, None

        latitude = location.getLatitude()
        longitude = location.getLongitude()

        if not (-90.0 <= latitude <= 90.0
                and -180.0 <= longitude <= 180.0):
            return INVALID_GPS, None, None

        return VALID_GPS, latitude, longitude

    except Throwable:
        return UNREADABLE, None, None
    except Exception:
        return UNREADABLE, None, None

class GeoEvidenceDataSourceFactory(IngestModuleFactoryAdapter):
    """Describe the GeoEvidence Data Source module to Autopsy."""

    def getModuleDisplayName(self):
        return MODULE_NAME

    def getModuleDescription(self):
        return (
            "Initial GeoEvidence data-source module. "
            "It finds and counts supported images and videos in the data source."
        )

    def getModuleVersionNumber(self):
        return "0.1"

    def isDataSourceIngestModuleFactory(self):
        return True

    def createDataSourceIngestModule(self, ingest_options):
        return GeoEvidenceDataSourceModule()


class GeoEvidenceDataSourceModule(DataSourceIngestModule):
    """Find supported media files and report their total."""

    logger = Logger.getLogger(MODULE_NAME)

    def __init__(self):
        self.context = None

    def log(self, level, message):
        self.logger.logp(
            level,
            self.__class__.__name__,
            inspect.stack()[1][3],
            message,
        )

    def startUp(self, context):
        self.context = context
        self.log(Level.INFO, "GeoEvidence Data Source started.")

    def process(self, data_source, progress_bar):
        case = Case.getCurrentCase()

        file_manager = case.getServices().getFileManager()

        media_files = []
        seen_file_ids = set()

        progress_bar.switchToIndeterminate()

        for extension in SUPPORTED_EXTENSIONS:
            pattern = "%" + extension

            for abstract_file in file_manager.findFiles(
                data_source,
                pattern,
            ):
                if abstract_file.isFile() == False:
                    continue

                file_name = abstract_file.getName().lower()

                if file_name.endswith(SUPPORTED_EXTENSIONS) == False:
                    continue

                file_id = abstract_file.getId()

                if file_id in seen_file_ids:
                    continue

                seen_file_ids.add(file_id)
                media_files.append(abstract_file)

        media_files.sort(
            key=lambda item: (item.getName().lower(), item.getId())
        )

        progress_bar.switchToDeterminate(len(media_files))

        for index, abstract_file in enumerate(media_files):
            if self.context.isJobCancelled():
                return IngestModule.ProcessResult.OK

            progress_bar.progress(index + 1)

        blackboard = case.getSleuthkitCase().getBlackboard()

        center = Coordinate(
            CENTER_LATITUDE,
            CENTER_LONGITUDE,
        )

        photos_with_valid_gps = 0
        photos_without_usable_gps = 0
        inside_radius = 0
        outside_radius = 0
        bookmarks_created = 0
        bookmarks_already_present = 0
        inside_items_created = 0
        inside_items_already_present = 0
        photos_no_gps = 0
        photos_invalid_gps = 0
        photos_unreadable = 0

        for source_file in media_files:
            if self.context.isJobCancelled():
                return IngestModule.ProcessResult.OK

            if not source_file.getName().lower().endswith(
                PHOTO_EXTENSIONS
            ):
                continue

            status, latitude, longitude = read_photo_gps(source_file)

            if status == NO_GPS:
                photos_no_gps += 1
                continue

            if status == INVALID_GPS:
                photos_invalid_gps += 1
                continue

            if status == UNREADABLE:
                photos_unreadable += 1
                continue

            point = Coordinate(latitude, longitude)

            distance_km = point.distance_to(center, "km")

            if distance_km <= RADIUS_KM:
                classification = "INSIDE_RADIUS"
                inside_radius += 1
            else:
                classification = "OUTSIDE_RADIUS"
                outside_radius += 1

            photos_with_valid_gps += 1

            attributes = ArrayList()

            attributes.add(
                BlackboardAttribute(
                    BlackboardAttribute.Type.TSK_GEO_LATITUDE,
                    MODULE_NAME,
                    point.lat,
                )
            )

            attributes.add(
                BlackboardAttribute(
                    BlackboardAttribute.Type.TSK_GEO_LONGITUDE,
                    MODULE_NAME,
                    point.lon,
                )
            )

            attributes.add(
                BlackboardAttribute(
                    BlackboardAttribute.Type.TSK_NAME,
                    MODULE_NAME,
                    source_file.getName(),
                )
            )

            attributes.add(
                BlackboardAttribute(
                    BlackboardAttribute.Type.TSK_COMMENT,
                    MODULE_NAME,
                    "Distance: %.3f km | %s" % (
                        distance_km,
                        classification,
                    ),
                )
            )

            if classification == "INSIDE_RADIUS":
                inside_attributes = ArrayList()

                inside_attributes.add(
                    BlackboardAttribute(
                        BlackboardAttribute.Type.TSK_SET_NAME,
                        MODULE_NAME,
                        "GeoEvidence - Inside radius",
                    )
                )

                inside_attributes.add(
                    BlackboardAttribute(
                        BlackboardAttribute.Type.TSK_COMMENT,
                        MODULE_NAME,
                        "Distance: %.3f km | INSIDE_RADIUS" % (
                            distance_km,
                        ),
                    )
                )

                if blackboard.artifactExists(
                    source_file,
                    BlackboardArtifact.Type.TSK_INTERESTING_ITEM,
                    inside_attributes,
                ):
                    inside_items_already_present += 1
                else:
                    try:
                        inside_item = source_file.newAnalysisResult(
                            BlackboardArtifact.Type.TSK_INTERESTING_ITEM,
                            Score.SCORE_LIKELY_NOTABLE,
                            None,
                            "GeoEvidence - Inside radius",
                            None,
                            inside_attributes,
                        ).getAnalysisResult()

                        blackboard.postArtifact(
                            inside_item,
                            MODULE_NAME,
                        )

                        inside_items_created += 1

                    except Exception as error:
                        self.log(
                            Level.SEVERE,
                            "Unable to create inside-radius result for "
                            + source_file.getName()
                            + ": "
                            + str(error),
                        )

            if blackboard.artifactExists(
                source_file,
                BlackboardArtifact.Type.TSK_GPS_BOOKMARK,
                attributes,
            ):
                bookmarks_already_present += 1
                continue

            try:
                bookmark = source_file.newDataArtifact(
                    BlackboardArtifact.Type.TSK_GPS_BOOKMARK,
                    attributes,
                )

                blackboard.postArtifact(
                    bookmark,
                    MODULE_NAME,
                )

                bookmarks_created += 1

            except Exception as error:
                self.log(
                    Level.SEVERE,
                    "Unable to create GPS bookmark for "
                    + source_file.getName()
                    + ": "
                    + str(error),
                )

        message = IngestMessage.createMessage(
            IngestMessage.MessageType.DATA,
            MODULE_NAME,
            (
                "Media: "
                + str(len(media_files))
                + " | GPS: "
                + str(photos_with_valid_gps)
                + " | Inside: "
                + str(inside_radius)
                + " | Outside: "
                + str(outside_radius)
                + " | New bookmarks: "
                + str(bookmarks_created)
                + " | Existing bookmarks: "
                + str(bookmarks_already_present)
                + " | New inside items: "
                + str(inside_items_created)
                + " | Existing inside items: "
                + str(inside_items_already_present)
                + " | No GPS: "
                + str(photos_no_gps)
                + " | Invalid GPS: "
                + str(photos_invalid_gps)
                + " | Unreadable: "
                + str(photos_unreadable)
            ),
        )

        IngestServices.getInstance().postMessage(message)

        return IngestModule.ProcessResult.OK

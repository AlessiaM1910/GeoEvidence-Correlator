"""GeoEvidence Data Source Ingest Module for Autopsy.

Finds JPEG and MP4/MOV files in a data source and checks whether their
GPS position falls inside a search radius around a given center.

Photos are read directly with the metadata-extractor library bundled
with Autopsy. Videos are exported to a temporary copy and read with
ExifTool. No other ingest module (for example Picture Analyzer) has to
run first.

For every file with valid GPS coordinates the module creates a GPS
Bookmark. Files inside the radius also get an Interesting Item. Both
record the center and the radius used, so a run with different
parameters creates new results instead of being skipped.

Center and the ExifTool path are fixed constants for now. The search
radius is set in the module settings before the ingest.
"""

import inspect
import json
import os
import math
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
from com.drew.metadata.exif import ExifIFD0Directory
from com.drew.metadata.exif import ExifSubIFDDirectory
from java.io import File
from java.lang import ProcessBuilder
from java.util.concurrent import TimeUnit
from org.sleuthkit.autopsy.datamodel import ContentUtils

from javax.swing import BoxLayout
from javax.swing import JLabel
from javax.swing import JTextField
from javax.swing import JButton
from javax.swing import JFileChooser
from javax.swing import JPanel
from org.sleuthkit.autopsy.ingest import GenericIngestModuleJobSettings
from org.sleuthkit.autopsy.ingest import IngestModuleIngestJobSettingsPanel
from org.sleuthkit.autopsy.ingest.IngestModule import IngestModuleException

from video_loader import (
    EXIFTOOL_FIELDS,
    INVALID_GPS,
    NO_GPS,
    SUPPORTED_VIDEO_TYPES,
    VALID_GPS,
    VIDEO_EXTENSION,
    classify_video_metadata)

MODULE_NAME = "GeoEvidence Data Source"

# JPEG and MP4/MOV are the validated first scope of the project.
SUPPORTED_EXTENSIONS = (".jpg", ".jpeg", ".mp4", ".mov")
DEFAULT_RADIUS_KM = 1.0
SETTING_CENTER_LAT = "center_lat"
SETTING_CENTER_LON = "center_lon"
SETTING_RADIUS = "radius_km"
SETTING_EXIFTOOL= "exiftool_path"
PHOTO_EXTENSIONS = (".jpg", ".jpeg")

UNREADABLE = "UNREADABLE"
UNKNOWN_DATE = "Unknown date"

EXIFTOOL_TIMEOUT_SECONDS = 60


def read_text(path):
    handle = open(path, "r")
    try:
        return handle.read()
    finally:
        handle.close()


def remove_quietly(path):
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass

def parse_radius_km(text):
    """Convert the radius typed by the user into a positive number."""
    if text is None:
        raise ValueError("The radius is empty.")

    try:
        radius = float(text.strip().replace(",", "."))
    except ValueError:
        raise ValueError("The radius must be a number.")

    if math.isnan(radius) or math.isinf(radius) or radius <= 0:
        raise ValueError("The radius must be greater than zero.")

    return radius

def find_exiftool():
    """Look for ExifTool in EXIFTOOL_PATH and in the PATH variable."""
    candidate = os.environ.get("EXIFTOOL_PATH")
    if candidate and os.path.isfile(candidate):
        return candidate

    for folder in os.environ.get("PATH", "").split(os.pathsep):
        for name in ("exiftool.exe", "exiftool"):
            path = os.path.join(folder, name)
            if os.path.isfile(path):
                return path

    return ""

def parse_center(latitude_text, longitude_text):
    """Build the search center from the two texts typed by the user."""
    latitude = (latitude_text or "").strip().replace(",", ".")
    longitude = (longitude_text or "").strip().replace(",", ".")

    if not latitude or not longitude:
        raise ValueError("Enter both the latitude and the longitude of the center.")

    return Coordinate(latitude, longitude)

def post_summary(text, message_type=IngestMessage.MessageType.INFO):
    """Show one short line in the Autopsy Ingest Inbox."""
    message = IngestMessage.createMessage(
        message_type,
        MODULE_NAME,
        text,
    )
    IngestServices.getInstance().postMessage(message)

def read_video_gps(abstract_file, work_directory, exiftool_path):
    """Return (status, latitude, longitude) for one video via ExifTool."""
    name = abstract_file.getName().lower()
    extension = ".mov" if name.endswith(".mov") else ".mp4"

    base = os.path.join(work_directory, str(abstract_file.getId()))
    video_copy = base + extension
    out_path = base + ".out.txt"
    err_path = base + ".err.txt"

    try:
        ContentUtils.writeToFile(abstract_file, File(video_copy))

        command = ArrayList()
        command.add(exiftool_path)
        command.add("-j")
        command.add("-n")
        command.add("-s")
        for field in EXIFTOOL_FIELDS:
            command.add(field)
        command.add(video_copy)

        builder = ProcessBuilder(command)
        builder.redirectOutput(File(out_path))
        builder.redirectError(File(err_path))
        process = builder.start()

        if not process.waitFor(EXIFTOOL_TIMEOUT_SECONDS, TimeUnit.SECONDS):
            process.destroyForcibly()
            return UNREADABLE, None, None, UNKNOWN_DATE

        if process.exitValue() != 0:
            return UNREADABLE, None, None, UNKNOWN_DATE

        metadata_list = json.loads(read_text(out_path))
        if not metadata_list:
            return UNREADABLE, None, None, UNKNOWN_DATE

        metadata = metadata_list[0]
        if metadata.get("FileType") not in SUPPORTED_VIDEO_TYPES:
            return UNREADABLE, None, None, UNKNOWN_DATE

        status, latitude, longitude, timestamp = (classify_video_metadata(metadata))
        return status, latitude, longitude, timestamp

    except Throwable:
        return UNREADABLE, None, None, UNKNOWN_DATE
    except Exception:
        return UNREADABLE, None, None, UNKNOWN_DATE
    finally:
        remove_quietly(video_copy)
        remove_quietly(out_path)
        remove_quietly(err_path)

def read_photo_timestamp(metadata):
    """Return the best date found in the photo metadata."""
    try:
        subifd = metadata.getFirstDirectoryOfType(ExifSubIFDDirectory)
        if subifd is not None:
            for tag in (
                ExifSubIFDDirectory.TAG_DATETIME_ORIGINAL,
                ExifSubIFDDirectory.TAG_DATETIME_DIGITIZED,
            ):
                value = subifd.getString(tag)
                if value and not is_zero_date(value):
                    return value

        ifd0 = metadata.getFirstDirectoryOfType(ExifIFD0Directory)
        if ifd0 is not None:
            value = ifd0.getString(ExifIFD0Directory.TAG_DATETIME)
            if value and not is_zero_date(value):
                return value

    except Throwable:
        pass
    except Exception:
        pass

    return UNKNOWN_DATE

def read_photo_gps(abstract_file):
    """Return (status, latitude, longitude, timestamp) for one photo."""
    timestamp = UNKNOWN_DATE
    try:
        stream = ReadContentInputStream(abstract_file)
        try:
            metadata = ImageMetadataReader.readMetadata(stream)
        finally:
            stream.close()

        timestamp = read_photo_timestamp(metadata)

        gps = metadata.getFirstDirectoryOfType(GpsDirectory)
        if gps is None:
            return NO_GPS, None, None, timestamp

        location = gps.getGeoLocation()
        if location is None:
            return INVALID_GPS, None, None, timestamp

        latitude = location.getLatitude()
        longitude = location.getLongitude()

        if not (-90.0 <= latitude <= 90.0
                and -180.0 <= longitude <= 180.0):
            return INVALID_GPS, None, None, timestamp

        return VALID_GPS, latitude, longitude, timestamp

    except Throwable:
        return UNREADABLE, None, None, UNKNOWN_DATE
    except Exception:
        return UNREADABLE, None, None, UNKNOWN_DATE

class GeoEvidenceSettingsPanel(IngestModuleIngestJobSettingsPanel):
    """Panel shown next to the module in the ingest configuration."""

    def __init__(self, settings):
        self.local_settings = settings
        self.initComponents()
        self.customizeComponents()

    def add_field(self, label_text, columns=12):
        """Add a label and a text box, and return the text box."""
        self.add(JLabel(label_text))
        field = JTextField(columns)
        field.setMaximumSize(field.getPreferredSize())
        self.add(field)
        return field

    def add_path_field(self, label_text, columns):
        """Add a label, a text box and a Browse button; return the box."""
        self.add(JLabel(label_text))

        row = JPanel()
        row.setLayout(BoxLayout(row, BoxLayout.X_AXIS))
        row.setAlignmentX(0.0)

        field = JTextField(columns)
        field.setMaximumSize(field.getPreferredSize())
        row.add(field)

        browse_button = JButton(
            "Browse...", actionPerformed=self.browse_exiftool
        )
        row.add(browse_button)

        self.add(row)
        return field

    def browse_exiftool(self, event):
        """Let the user pick exiftool.exe with a file dialog."""
        chooser = JFileChooser()

        current = self.exiftool_field.getText().strip().strip('"')
        if current:
            chooser.setSelectedFile(File(current))

        if chooser.showOpenDialog(self) == JFileChooser.APPROVE_OPTION:
            self.exiftool_field.setText(
                chooser.getSelectedFile().getAbsolutePath()
            )

    def initComponents(self):
        self.setLayout(BoxLayout(self, BoxLayout.Y_AXIS))
        self.latitude_field = self.add_field(
            "Center latitude (example: 45.4642):")
        self.longitude_field = self.add_field(
            "Center longitude (example: 9.1900):")
        self.radius_field = self.add_field(
            "Search radius (km), default %g:" % DEFAULT_RADIUS_KM)
        self.exiftool_field = self.add_path_field(
            "ExifTool path (needed for videos):", 14)

    def saved_value(self, key, default):
        value = self.local_settings.getSetting(key)
        if not value:
            return str(default)
        return value

    def customizeComponents(self):
        self.latitude_field.setText(
            self.saved_value(SETTING_CENTER_LAT, "")
        )
        self.longitude_field.setText(
            self.saved_value(SETTING_CENTER_LON, "")
        )
        self.radius_field.setText(
            self.saved_value(SETTING_RADIUS, DEFAULT_RADIUS_KM)
        )
        self.exiftool_field.setText(
            self.saved_value(SETTING_EXIFTOOL, find_exiftool())
        )

    def getSettings(self):
        self.local_settings.setSetting(
            SETTING_CENTER_LAT, self.latitude_field.getText()
        )
        self.local_settings.setSetting(
            SETTING_CENTER_LON, self.longitude_field.getText()
        )
        self.local_settings.setSetting(
            SETTING_RADIUS, self.radius_field.getText()
        )
        self.local_settings.setSetting(
            SETTING_EXIFTOOL, self.exiftool_field.getText()
        )
        return self.local_settings
    
class GeoEvidenceDataSourceFactory(IngestModuleFactoryAdapter):
    """Describe the GeoEvidence Data Source module to Autopsy."""

    def getModuleDisplayName(self):
        return MODULE_NAME

    def getModuleDescription(self):
        return (
            "Finds geotagged photos and videos and flags those "
            "inside a search radius."
        )

    def getModuleVersionNumber(self):
        return "0.1"

    def isDataSourceIngestModuleFactory(self):
        return True

    def getDefaultIngestJobSettings(self):
        settings = GenericIngestModuleJobSettings()
        settings.setSetting(SETTING_CENTER_LAT, "")
        settings.setSetting(SETTING_CENTER_LON, "")
        settings.setSetting(SETTING_RADIUS, str(DEFAULT_RADIUS_KM))
        settings.setSetting(SETTING_EXIFTOOL, find_exiftool())
        return settings

    def hasIngestJobSettingsPanel(self):
        return True

    def getIngestJobSettingsPanel(self, settings):
        if not isinstance(settings, GenericIngestModuleJobSettings):
            settings = self.getDefaultIngestJobSettings()
        return GeoEvidenceSettingsPanel(settings)

    def createDataSourceIngestModule(self, settings):
        if not isinstance(settings, GenericIngestModuleJobSettings):
            settings = self.getDefaultIngestJobSettings()
        return GeoEvidenceDataSourceModule(settings)


class GeoEvidenceDataSourceModule(DataSourceIngestModule):
    """Find supported media files and report their total."""

    logger = Logger.getLogger(MODULE_NAME)

    def __init__(self,settings):
        self.context = None
        self.local_settings = settings 
        self.radius_km= DEFAULT_RADIUS_KM
        self.center = None
        self.exiftool_path= ""

    def log(self, level, message):
        self.logger.logp(
            level,
            self.__class__.__name__,
            inspect.stack()[1][3],
            message,
        )

    def setting_text(self, key, default):
        value = self.local_settings.getSetting(key)
        if not value:
            return str(default)
        return value

    def startUp(self, context):
        self.context = context

        radius_text = self.setting_text(SETTING_RADIUS, DEFAULT_RADIUS_KM)
        latitude_text = self.setting_text(SETTING_CENTER_LAT, "")
        longitude_text = self.setting_text(SETTING_CENTER_LON, "")
        exiftool_text = self.setting_text(SETTING_EXIFTOOL, find_exiftool())
        self.exiftool_path = exiftool_text.strip().strip('"')

        try:
            self.radius_km = parse_radius_km(radius_text)
        except ValueError as error:
            raise IngestModuleException(
                "GeoEvidence: invalid radius '%s'. %s" % (radius_text, error)
            )

        try:
            self.center = parse_center(latitude_text, longitude_text)
        except ValueError as error:
            raise IngestModuleException(
                "GeoEvidence: invalid center (latitude '%s', longitude '%s'). %s"
                % (latitude_text, longitude_text, error)
            )

        self.log(
            Level.INFO,
            "GeoEvidence Data Source started. Center: %s, %s Radius: %s km"
            % (self.center.lat, self.center.lon, self.radius_km),
        )

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

        media_files.sort(key=lambda item: (item.getName().lower(), item.getId()))

        progress_bar.switchToDeterminate(len(media_files))

        blackboard = case.getSleuthkitCase().getBlackboard()

        center = self.center

        radius_label = "%g km" % self.radius_km
        inside_set_name = ("GeoEvidence - Inside radius (%s around %.4f, %.4f)"
            % (radius_label, center.lat, center.lon))
        
        parameters = "Center: %.6f, %.6f | Radius: %.3f km" % (center.lat, center.lon, self.radius_km)
        
        work_directory = os.path.join(case.getTempDirectory(), "geoevidence")
        
        exiftool_available = os.path.isfile(self.exiftool_path)

        videos_skipped = 0

        if not os.path.exists(work_directory):
            try:
                os.makedirs(work_directory)
            except Exception:
                pass

        media_with_valid_gps = 0
        inside_radius = 0
        outside_radius = 0
        bookmarks_created = 0
        bookmarks_already_present = 0
        inside_items_created = 0
        inside_items_already_present = 0
        media_no_gps = 0
        media_invalid_gps = 0
        media_unreadable = 0

        for index, source_file in enumerate(media_files):
            if self.context.isJobCancelled():
                return IngestModule.ProcessResult.OK

            progress_bar.progress(index + 1)

            file_name = source_file.getName().lower()

            if file_name.endswith(PHOTO_EXTENSIONS):
                status, latitude, longitude, timestamp = read_photo_gps(source_file)
            elif file_name.endswith(VIDEO_EXTENSION):
                if not exiftool_available:
                    videos_skipped += 1
                    continue
                status, latitude, longitude, timestamp = read_video_gps(source_file, work_directory, self.exiftool_path)
            else:
                continue

            if status == NO_GPS:
                media_no_gps += 1
                continue

            if status == INVALID_GPS:
                media_invalid_gps += 1
                continue

            if status == UNREADABLE:
                media_unreadable += 1
                continue

            point = Coordinate(latitude, longitude)

            distance_km = point.distance_to(center, "km")

            if distance_km <= self.radius_km:
                classification = "INSIDE_RADIUS"
                inside_radius += 1
            else:
                classification = "OUTSIDE_RADIUS"
                outside_radius += 1

            media_with_valid_gps += 1

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
                    "%s (%s)" % (source_file.getName(), radius_label),
                )
            )

            attributes.add(
                BlackboardAttribute(
                    BlackboardAttribute.Type.TSK_COMMENT,
                    MODULE_NAME,
                    "Radius: %s | Distance: %.3f km | %s | %s" % (
                        radius_label,
                        distance_km,
                        classification,
                        parameters,
                    ),
                )
            )

            if classification == "INSIDE_RADIUS":
                inside_attributes = ArrayList()

                inside_attributes.add(
                    BlackboardAttribute(
                        BlackboardAttribute.Type.TSK_SET_NAME,
                        MODULE_NAME,
                        inside_set_name,
                    )
                )

                inside_attributes.add(
                    BlackboardAttribute(
                        BlackboardAttribute.Type.TSK_COMMENT,
                        MODULE_NAME,
                        "Radius: %s | Distance: %.3f km | INSIDE_RADIUS | %s" % (
                            radius_label,
                            distance_km,
                            parameters,
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
                            inside_set_name,
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

        post_summary("Parameters: " + parameters)
        post_summary(
            "Media: %d | GPS: %d | Inside: %d | Outside: %d" % (
                len(media_files),
                media_with_valid_gps,
                inside_radius,
                outside_radius,
            )
        )

        post_summary(
            "Bookmarks: %d new, %d existing"
            " | Inside items: %d new, %d existing" % (
                bookmarks_created,
                bookmarks_already_present,
                inside_items_created,
                inside_items_already_present,
            )
        )

        post_summary(
            "Not usable: No GPS %d | Invalid GPS %d | Unreadable %d" % (
                media_no_gps,
                media_invalid_gps,
                media_unreadable,
            )
        )

        if videos_skipped > 0:
            self.log(
                Level.SEVERE,
                "ExifTool not found at " + self.exiftool_path
                + ": " + str(videos_skipped) + " video(s) skipped.",
            )
            post_summary(
                "WARNING: ExifTool not found (set its path in the module "
                "settings), %d video(s) skipped" % videos_skipped,
                IngestMessage.MessageType.WARNING,
            )

        return IngestModule.ProcessResult.OK

"""First Data Source Ingest Module for GeoEvidence.

This checkpoint only discovers supported media and reports their count. This checkpoint counts supported media and reads existing EXIF coordinate
results produced by Picture Analyzer. It does not yet invoke ExifTool or
create GeoEvidence Blackboard artifacts.
"""

import inspect

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


MODULE_NAME = "GeoEvidence Data Source"

# JPEG and MP4/MOV are the validated first scope of the project.
SUPPORTED_EXTENSIONS = (".jpg", ".jpeg", ".mp4", ".mov")


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
        """Find JPEG, MP4 and MOV files in one Autopsy data source."""

        file_manager = Case.getCurrentCase().getServices().getFileManager()
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

            self.log(
                Level.INFO,
                "Media file found: " + abstract_file.getName(),
            )

            progress_bar.progress(index + 1)

        blackboard = (
            Case.getCurrentCase()
            .getSleuthkitCase()
            .getBlackboard()
        )

        exif_artifacts = blackboard.getArtifacts(
            BlackboardArtifact.Type.TSK_METADATA_EXIF.getTypeID(),
            data_source.getId(),
        )

        photos_with_valid_gps = 0
        photos_without_usable_gps = 0

        for artifact in exif_artifacts:
            latitude_attribute = artifact.getAttribute(
                BlackboardAttribute.Type.TSK_GEO_LATITUDE
            )

            longitude_attribute = artifact.getAttribute(
                BlackboardAttribute.Type.TSK_GEO_LONGITUDE
            )

            if (
                latitude_attribute is not None
                and longitude_attribute is not None
            ):
                photos_with_valid_gps += 1
            else:
                photos_without_usable_gps += 1

        message = IngestMessage.createMessage(
            IngestMessage.MessageType.DATA,
            MODULE_NAME,
            ("Media files found: "
                + str(len(media_files))
                + " | EXIF artifacts: "
                + str(len(exif_artifacts))
                + " | Photos with valid GPS: "
                + str(photos_with_valid_gps)
                + " | Photos without usable GPS: "
                + str(photos_without_usable_gps)
            ),
        )

        IngestServices.getInstance().postMessage(message)

        return IngestModule.ProcessResult.OK

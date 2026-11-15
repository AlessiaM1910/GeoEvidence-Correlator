"""Minimal GeoEvidence File Ingest Module for Autopsy."""

import inspect

from java.util import Arrays
from java.util.logging import Level

from org.sleuthkit.autopsy.casemodule import Case
from org.sleuthkit.autopsy.coreutils import Logger
from org.sleuthkit.autopsy.ingest import FileIngestModule
from org.sleuthkit.autopsy.ingest import IngestMessage
from org.sleuthkit.autopsy.ingest import IngestModule
from org.sleuthkit.autopsy.ingest import IngestModuleFactoryAdapter
from org.sleuthkit.autopsy.ingest import IngestServices
from org.sleuthkit.datamodel import BlackboardArtifact
from org.sleuthkit.datamodel import BlackboardAttribute
from org.sleuthkit.datamodel import Score


class GeoEvidenceFileIngestModuleFactory(IngestModuleFactoryAdapter):
    """Provide Autopsy with the module metadata and module instances."""

    module_name = "GeoEvidence File Ingest"

    def getModuleDisplayName(self):
        """Return the name displayed in Autopsy."""
        return self.module_name

    def getModuleDescription(self):
        """Return a brief description displayed in Autopsy."""
        return (
            "Initial GeoEvidence prototype. "
            "It verifies that Autopsy can load and execute the module."
        )

    def getModuleVersionNumber(self):
        """Return the module version."""
        return "0.1"

    def isFileIngestModuleFactory(self):
        """Declare that this factory creates a File Ingest Module."""
        return True

    def createFileIngestModule(self, ingest_options):
        """Create one ingest-module instance for an Autopsy worker thread."""
        return GeoEvidenceFileIngestModule()


class GeoEvidenceFileIngestModule(FileIngestModule):
    """Create a visible test artifact for every regular file received."""

    logger = Logger.getLogger(
        GeoEvidenceFileIngestModuleFactory.module_name
    )

    def log(self, level, message):
        """Write a message to the Autopsy application log."""
        self.logger.logp(
            level,
            self.__class__.__name__,
            inspect.stack()[1][3],
            message,
        )

    def startUp(self, context):
        """Initialize the module before Autopsy starts passing files to it."""
        self.processed_file_count = 0
        self.log(Level.INFO, "GeoEvidence File Ingest started.")

    def process(self, file):
        """Create a test analysis result associated with each regular file."""
        if file.isFile() == False:
            return IngestModule.ProcessResult.OK

        self.processed_file_count += 1

        artifact = file.newAnalysisResult(
            BlackboardArtifact.Type.TSK_INTERESTING_ITEM,
            Score.SCORE_UNKNOWN,
            None,
            "GeoEvidence Prototype Files",
            None,
            Arrays.asList(
                BlackboardAttribute(
                    BlackboardAttribute.Type.TSK_SET_NAME,
                    GeoEvidenceFileIngestModuleFactory.module_name,
                    "GeoEvidence Prototype Files",
                )
            ),
        ).getAnalysisResult()

        blackboard = Case.getCurrentCase().getSleuthkitCase().getBlackboard()

        try:
            blackboard.postArtifact(
                artifact,
                GeoEvidenceFileIngestModuleFactory.module_name,
            )
        except Exception as error:
            self.log(
                Level.SEVERE,
                "Unable to publish artifact for "
                + file.getName()
                + ": "
                + str(error),
            )

        return IngestModule.ProcessResult.OK

    def shutDown(self):
        """Send a completion message when this module instance stops."""
        message = IngestMessage.createMessage(
            IngestMessage.MessageType.DATA,
            GeoEvidenceFileIngestModuleFactory.module_name,
            "GeoEvidence prototype completed. Files received: "
            + str(self.processed_file_count),
        )

        IngestServices.getInstance().postMessage(message)
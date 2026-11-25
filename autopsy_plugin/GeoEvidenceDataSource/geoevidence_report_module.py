"""GeoEvidence report module: appears in Autopsy's Generate Report."""

from java.lang import Throwable
from javax.swing import BoxLayout
from javax.swing import ButtonGroup
from javax.swing import JLabel
from javax.swing import JPanel
from javax.swing import JRadioButton

from org.sleuthkit.autopsy.casemodule import Case
from org.sleuthkit.autopsy.report import GeneralReportModuleAdapter
from org.sleuthkit.autopsy.report import ReportProgressPanel

from geoevidence_report import save_summary_report
from geoevidence_report import save_verbose_report
from geoevidence_results import register_result_types

REPORT_MODULE_NAME = "GeoEvidence Report"
SUMMARY_FILE_NAME = "GeoEvidence_summary.html"
VERBOSE_FILE_NAME = "GeoEvidence_verbose.html"


class GeoEvidenceReportModule(GeneralReportModuleAdapter):
    """Writes the GeoEvidence reports from the results saved in the case."""

    def __init__(self):
        self.summary_button = None
        self.verbose_button = None
        self.both_button = None

    def getName(self):
        return REPORT_MODULE_NAME

    def getDescription(self):
        return ("Summary and verbose report of all the GeoEvidence runs "
                "saved in the case.")

    def getRelativeFilePath(self):
        if self.selected_type() == "verbose":
            return VERBOSE_FILE_NAME
        return SUMMARY_FILE_NAME

    def getConfigurationPanel(self):
        panel = JPanel()
        panel.setLayout(BoxLayout(panel, BoxLayout.Y_AXIS))
        panel.add(JLabel("Report type:"))

        self.summary_button = JRadioButton("Summary")
        self.verbose_button = JRadioButton("Verbose")
        self.both_button = JRadioButton("Both", True)

        group = ButtonGroup()
        for button in (self.summary_button, self.verbose_button,
                       self.both_button):
            group.add(button)
            panel.add(button)

        return panel

    def selected_type(self):
        if self.summary_button is not None and \
                self.summary_button.isSelected():
            return "summary"
        if self.verbose_button is not None and \
                self.verbose_button.isSelected():
            return "verbose"
        return "both"

    def generateReport(self, settings_or_directory, progress_panel):
        # Autopsy may pass the settings object instead of the folder path.
        if hasattr(settings_or_directory, "getReportDirectoryPath"):
            base_report_dir = settings_or_directory.getReportDirectoryPath()
        else:
            base_report_dir = settings_or_directory

        progress_panel.setIndeterminate(True)
        progress_panel.start()
        progress_panel.updateStatusLabel("Reading the GeoEvidence results...")

        try:
            case = Case.getCurrentCase()
            blackboard = case.getSleuthkitCase().getBlackboard()
            types = register_result_types(blackboard)
            chosen = self.selected_type()
            written = 0

            if chosen in ("summary", "both"):
                progress_panel.updateStatusLabel("Writing the summary report...")
                path = save_summary_report(
                    case, blackboard, types,
                    report_directory=base_report_dir,
                    file_name=SUMMARY_FILE_NAME,
                )
                if path is not None:
                    case.addReport(
                        path, REPORT_MODULE_NAME, "GeoEvidence summary report"
                    )
                    written += 1

            if chosen in ("verbose", "both"):
                progress_panel.updateStatusLabel("Writing the verbose report...")
                path = save_verbose_report(
                    case, blackboard, types,
                    report_directory=base_report_dir,
                    file_name=VERBOSE_FILE_NAME,
                )
                if path is not None:
                    case.addReport(
                        path, REPORT_MODULE_NAME, "GeoEvidence verbose report"
                    )
                    written += 1

            if written == 0:
                progress_panel.complete(
                    ReportProgressPanel.ReportStatus.ERROR,
                    "No GeoEvidence results in this case: "
                    "run the GeoEvidence ingest module first.",
                )
                return

            progress_panel.complete(ReportProgressPanel.ReportStatus.COMPLETE)

        except Throwable as error:
            progress_panel.complete(
                ReportProgressPanel.ReportStatus.ERROR, "Error: %s" % error
            )
        except Exception as error:
            progress_panel.complete(
                ReportProgressPanel.ReportStatus.ERROR, "Error: %s" % error
            )
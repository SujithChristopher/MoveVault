# ui/subject_mapping_dialog.py
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, QDialogButtonBox, QMessageBox
from PySide6.QtGui import QFont

class SubjectMappingDialog(QDialog):
    def __init__(self, mismatch_subjects, existing_subjects, parent=None):
        super().__init__(parent)
        self.mismatch_subjects = mismatch_subjects
        self.existing_subjects = existing_subjects
        self.subject_mapping = {}

        self.setWindowTitle("Subject Name Mapping")
        self.setMinimumSize(600, 400)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        title_label = QLabel("Subject Name Mapping")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        desc_label = QLabel(
            "Some subject names from ActiGraph files don't match existing S3 folders.\n"
            "Please map them to the correct existing subjects or create new folders."
        )
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)

        self.mapping_table = QTableWidget()
        self.mapping_table.setColumnCount(3)
        self.mapping_table.setHorizontalHeaderLabels(["ActiGraph Subject", "File Count", "Map to Existing Subject"])

        header = self.mapping_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)

        self.populate_mapping_table()
        layout.addWidget(self.mapping_table)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def populate_mapping_table(self):
        self.mapping_table.setRowCount(len(self.mismatch_subjects))

        for row, (subject, count) in enumerate(self.mismatch_subjects.items()):
            self.mapping_table.setItem(row, 0, QTableWidgetItem(subject))
            self.mapping_table.setItem(row, 1, QTableWidgetItem(str(count)))

            combo = QComboBox()
            combo.addItem("-- Select Existing Subject --")
            combo.addItems(self.existing_subjects)

            close_match = self.find_close_match(subject, self.existing_subjects)
            if close_match:
                combo.setCurrentText(close_match)

            self.mapping_table.setCellWidget(row, 2, combo)

    def find_close_match(self, subject, existing_subjects):
        subject_lower = subject.lower()
        for existing in existing_subjects:
            if existing.lower() == subject_lower:
                return existing
        for existing in existing_subjects:
            if subject_lower in existing.lower() or existing.lower() in subject_lower:
                return existing
        return None

    def get_mapping(self):
        mapping = {}
        for row in range(self.mapping_table.rowCount()):
            actigraph_subject = self.mapping_table.item(row, 0).text()
            combo = self.mapping_table.cellWidget(row, 2)
            selected_subject = combo.currentText()
            if selected_subject != "-- Select Existing Subject --":
                mapping[actigraph_subject] = selected_subject
            else:
                QMessageBox.warning(
                    self,
                    "Incomplete Mapping",
                    f"Please select an existing subject for '{actigraph_subject}'"
                )
                return None
        return mapping

from PySide6.QtWidgets import QApplication, QMessageBox
import sys
from ui.main_window import MoveVaultUploader
from ui.aws_config_dialog import AWSConfigDialog
from core.logger import AWS_ACCESS_KEY, AWS_SECRET_KEY

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    if AWS_ACCESS_KEY == "YOUR_ACCESS_KEY_HERE" or AWS_SECRET_KEY == "YOUR_SECRET_KEY_HERE":
        reply = QMessageBox.question(None, "AWS Configuration Required",
                                    "AWS credentials are not configured. Would you like to configure them now?\n\n"
                                    "You can also configure them later via Settings → AWS Configuration.",
                                    QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            # Show AWS configuration dialog
            config_dialog = AWSConfigDialog()
            if not config_dialog.exec():
                sys.exit(0)  # User cancelled configuration
        elif reply == QMessageBox.No:
            sys.exit(0)

    window = MoveVaultUploader()
    window.show()

    app.aboutToQuit.connect(window.logger.finalize_session)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
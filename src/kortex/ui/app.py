from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QObject, QUrl, Slot
from PySide6.QtGui import QAction, QIcon
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon


@dataclass(frozen=True)
class UiPaths:
    qml_dir: Path

    @property
    def main_qml(self) -> Path:
        return self.qml_dir / "Main.qml"


class AppController(QObject):
    def __init__(self, app: QApplication, engine: QQmlApplicationEngine) -> None:
        super().__init__()
        self._app = app
        self._engine = engine

    @Slot()
    def quitApp(self) -> None:
        self._app.quit()


def _find_ui_paths() -> UiPaths:
    # src/kortex/ui/app.py -> src/kortex/ui/qml
    qml_dir = Path(__file__).resolve().parent / "qml"
    return UiPaths(qml_dir=qml_dir)


def _create_tray(
    *,
    app: QApplication,
    show_main: callable,
    show_settings: callable,
    quit_app: callable,
) -> QSystemTrayIcon:
    icon = QIcon.fromTheme("assistant")
    if icon.isNull():
        icon = QIcon.fromTheme("applications-system")

    tray = QSystemTrayIcon(icon, parent=app)
    tray.setToolTip("Kortex")

    menu = QMenu()

    open_action = QAction("Open")
    open_action.triggered.connect(show_main)
    menu.addAction(open_action)

    settings_action = QAction("Settings")
    settings_action.triggered.connect(show_settings)
    menu.addAction(settings_action)

    menu.addSeparator()

    quit_action = QAction("Quit")
    quit_action.triggered.connect(quit_app)
    menu.addAction(quit_action)

    tray.setContextMenu(menu)

    def _on_activated(reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            show_main()

    tray.activated.connect(_on_activated)

    tray.show()
    return tray


def run_ui() -> int:
    app = QApplication([])
    app.setApplicationName("Kortex")
    app.setOrganizationName("Kortex")
    app.setQuitOnLastWindowClosed(False)

    engine = QQmlApplicationEngine()

    controller = AppController(app, engine)
    engine.rootContext().setContextProperty("App", controller)

    ui_paths = _find_ui_paths()
    main_qml_url = QUrl.fromLocalFile(str(ui_paths.main_qml))
    engine.load(main_qml_url)

    if not engine.rootObjects():
        raise RuntimeError(f"Failed to load QML: {ui_paths.main_qml}")

    root = engine.rootObjects()[0]

    def show_main() -> None:
        root.setProperty("visible", True)
        # Bring to front best-effort
        try:
            root.show()
            root.raise_()
            root.requestActivate()
        except Exception:
            pass

    def show_settings() -> None:
        root.setProperty("currentPage", 1)
        show_main()

    tray = _create_tray(
        app=app,
        show_main=show_main,
        show_settings=show_settings,
        quit_app=app.quit,
    )
    # Keep a reference so it doesn't get GC'd
    app._kortex_tray = tray  # type: ignore[attr-defined]

    return app.exec()
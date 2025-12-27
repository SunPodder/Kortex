import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Qt.labs.settings as Labs

Item {
    id: root

    Labs.Settings {
        id: appSettings
        category: "app"

        // Placeholder preferences for later wiring
        property bool startOnLogin: false
        property bool enableNotifications: true
        property bool darkMode: true
    }

    Column {
        anchors.fill: parent
        anchors.margins: 20
        spacing: 16

        Label {
            text: "Settings"
            font.pixelSize: 22
            font.bold: true
            color: "#e8edf7"
        }

        Rectangle {
            width: parent.width
            radius: 12
            color: "#151a22"
            border.color: "#2a3446"

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 14
                spacing: 10

                Label {
                    text: "App"
                    font.pixelSize: 16
                    font.bold: true
                    color: "#e8edf7"
                    Layout.fillWidth: true
                }

                Label {
                    text: "Closing the window will hide Kortex to the system tray. Right-click the tray icon to quit."
                    color: "#9aa5b8"
                    wrapMode: Text.WordWrap
                    font.pixelSize: 12
                    Layout.fillWidth: true
                }

                Rectangle {
                    Layout.fillWidth: true
                    height: 1
                    color: "#2a3446"
                }

                Switch {
                    text: "Start on login (coming soon)"
                    checked: appSettings.startOnLogin
                    onToggled: appSettings.startOnLogin = checked
                    enabled: false
                    Layout.fillWidth: true
                }

                Switch {
                    text: "Enable notifications"
                    checked: appSettings.enableNotifications
                    onToggled: appSettings.enableNotifications = checked
                    Layout.fillWidth: true
                }

                Switch {
                    text: "Dark mode"
                    checked: appSettings.darkMode
                    onToggled: appSettings.darkMode = checked
                    Layout.fillWidth: true
                }
            }
        }

        Rectangle {
            width: parent.width
            radius: 12
            color: "#151a22"
            border.color: "#2a3446"

            Column {
                anchors.fill: parent
                anchors.margins: 14
                spacing: 8

                Label {
                    text: "About"
                    font.pixelSize: 16
                    font.bold: true
                    color: "#e8edf7"
                }

                Label {
                    text: "Kortex AI Desktop Assistant"
                    color: "#aeb6c6"
                }

                Label {
                    text: "Version: 0.1.0"
                    color: "#aeb6c6"
                }

                Label {
                    text: "Build date: 2025-12-27"
                    color: "#aeb6c6"
                }
            }
        }
    }
}

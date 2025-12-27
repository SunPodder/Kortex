import QtQuick
import QtQuick.Controls

Rectangle {
    id: root
    color: "#151a22"
    radius: 10
    height: 50

    property string userName: "sunpodder"
    property string avatarText: "S"

    signal settingsClicked()

    MouseArea {
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: profileMenu.open()

        Rectangle {
            anchors.fill: parent
            radius: 10
            color: parent.containsMouse ? "#1a2533" : "transparent"
        }
    }

    Row {
        anchors.fill: parent
        anchors.margins: 8
        spacing: 10

        // Avatar
        Rectangle {
            width: 34
            height: 34
            radius: 17
            color: "#3a68b8"
            anchors.verticalCenter: parent.verticalCenter

            Label {
                anchors.centerIn: parent
                text: root.avatarText
                color: "#e8edf7"
                font.pixelSize: 16
                font.bold: true
            }
        }

        Column {
            anchors.verticalCenter: parent.verticalCenter
            spacing: 2

            Label {
                text: root.userName
                color: "#e8edf7"
                font.pixelSize: 14
                font.bold: true
            }
        }

        Item { width: 1; height: 1 }

        Label {
            text: "⋮"
            color: "#9aa5b8"
            font.pixelSize: 20
            anchors.verticalCenter: parent.verticalCenter
        }
    }

    Menu {
        id: profileMenu
        y: -profileMenu.height

        MenuItem {
            text: "⚙ Settings"
            onTriggered: root.settingsClicked()
        }

        MenuItem {
            text: "❓ Help"
            onTriggered: {
                // TODO: Open help
            }
        }
    }
}

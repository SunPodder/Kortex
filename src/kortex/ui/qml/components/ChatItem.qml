import QtQuick
import QtQuick.Controls

Item {
    id: root

    property string title: ""
    property string preview: ""
    property bool selected: false

    signal clicked()

    implicitHeight: 64

    Rectangle {
        anchors.fill: parent
        anchors.margins: 4
        radius: 8
        color: root.selected ? "#243149" : "transparent"

        MouseArea {
            anchors.fill: parent
            hoverEnabled: true
            onClicked: root.clicked()

            Rectangle {
                anchors.fill: parent
                radius: 8
                color: parent.containsMouse && !root.selected ? "#1b2230" : "transparent"
            }
        }

        Column {
            anchors.fill: parent
            anchors.margins: 10
            spacing: 4

            Label {
                text: root.title
                color: root.selected ? "#e8edf7" : "#aeb6c6"
                font.pixelSize: 13
                font.bold: root.selected
                elide: Text.ElideRight
                width: parent.width
            }

            Label {
                text: root.preview
                color: "#707a8a"
                font.pixelSize: 12
                elide: Text.ElideRight
                width: parent.width
            }
        }
    }
}

import QtQuick
import QtQuick.Controls

Item {
    id: root

    property string text: ""
    property string iconName: ""
    property bool selected: false

    signal clicked()

    implicitHeight: 44

    Rectangle {
        anchors.fill: parent
        radius: 10
        color: root.selected ? "#243149" : "transparent"
        border.color: root.selected ? "#2c3b58" : "transparent"
    }

    MouseArea {
        anchors.fill: parent
        hoverEnabled: true
        onClicked: root.clicked()

        Rectangle {
            anchors.fill: parent
            radius: 10
            color: parent.containsMouse && !root.selected ? "#1b2230" : "transparent"
            border.color: parent.containsMouse && !root.selected ? "#2a3446" : "transparent"
        }
    }

    Row {
        anchors.verticalCenter: parent.verticalCenter
        anchors.left: parent.left
        anchors.leftMargin: 12
        spacing: 10

        Label {
            text: root.iconName
            color: root.selected ? "#e8edf7" : "#aeb6c6"
            font.pixelSize: 14
            width: 20
            horizontalAlignment: Text.AlignHCenter
        }

        Label {
            text: root.text
            color: root.selected ? "#e8edf7" : "#aeb6c6"
            font.pixelSize: 14
            elide: Text.ElideRight
        }
    }
}

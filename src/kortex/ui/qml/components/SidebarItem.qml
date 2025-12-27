import QtQuick
import QtQuick.Controls

Item {
    id: root

    property string icon: ""
    property string text: ""
    property string badge: ""
    property bool selected: false

    signal clicked()

    implicitHeight: 40

    Rectangle {
        anchors.fill: parent
        anchors.margins: 2
        radius: 8
        color: root.selected ? "#2a3f5f" : "transparent"

        MouseArea {
            anchors.fill: parent
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor
            onClicked: root.clicked()

            Rectangle {
                anchors.fill: parent
                radius: 8
                color: parent.containsMouse && !root.selected ? "#1a2533" : "transparent"
            }
        }

        Row {
            anchors.verticalCenter: parent.verticalCenter
            anchors.left: parent.left
            anchors.leftMargin: 10
            anchors.right: parent.right
            anchors.rightMargin: 10
            spacing: 10

            Label {
                text: root.icon
                color: root.selected ? "#e8edf7" : "#9aa5b8"
                font.pixelSize: 16
                width: 20
                horizontalAlignment: Text.AlignHCenter
                anchors.verticalCenter: parent.verticalCenter
            }

            Label {
                text: root.text
                color: root.selected ? "#e8edf7" : "#9aa5b8"
                font.pixelSize: 14
                elide: Text.ElideRight
                width: parent.width - 60
                anchors.verticalCenter: parent.verticalCenter
            }

            Rectangle {
                visible: root.badge !== ""
                width: badgeLabel.width + 8
                height: 18
                radius: 9
                color: "#3a68b8"
                anchors.verticalCenter: parent.verticalCenter

                Label {
                    id: badgeLabel
                    anchors.centerIn: parent
                    text: root.badge
                    color: "#e8edf7"
                    font.pixelSize: 10
                    font.bold: true
                }
            }
        }
    }
}

import QtQuick
import QtQuick.Controls

Item {
    id: root

    property string text: ""
    property bool isUser: false

    implicitHeight: bubbleRect.height + 16
    implicitWidth: parent.width

    Rectangle {
        id: bubbleRect
        anchors.left: root.isUser ? undefined : parent.left
        anchors.right: root.isUser ? parent.right : undefined
        anchors.margins: 8
        width: Math.min(parent.width * 0.75, messageLabel.implicitWidth + 24)
        height: messageLabel.implicitHeight + 20
        radius: 12
        color: root.isUser ? "#2c5aa0" : "#1b2230"
        border.color: root.isUser ? "#3a68b8" : "#2a3446"

        Label {
            id: messageLabel
            anchors.fill: parent
            anchors.margins: 12
            text: root.text
            color: "#e8edf7"
            wrapMode: Text.WordWrap
            font.pixelSize: 14
        }
    }
}

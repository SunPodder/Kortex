import QtQuick
import QtQuick.Controls

Rectangle {
    id: root
    color: "#151a22"
    radius: 10
    height: 50

    property string userName: UserInfo ? UserInfo.username : "User"
    property string avatarText: userName.length > 0 ? userName.charAt(0).toUpperCase() : "U"
    property string avatarPath: UserInfo ? UserInfo.avatarPath : ""

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

    // Avatar and name on the left
    Row {
        anchors.left: parent.left
        anchors.leftMargin: 12
        anchors.verticalCenter: parent.verticalCenter
        spacing: 8

        // Avatar
        Rectangle {
            width: 34
            height: 34
            radius: 17
            color: "#3a68b8"
            anchors.verticalCenter: parent.verticalCenter
            clip: true

            Image {
                id: avatarImage
                anchors.fill: parent
                source: root.avatarPath !== "" ? "file://" + root.avatarPath : ""
                visible: status === Image.Ready
                fillMode: Image.PreserveAspectCrop
                smooth: true
                layer.enabled: true
                layer.smooth: true
            }

            Label {
                anchors.centerIn: parent
                text: root.avatarText
                color: "#e8edf7"
                font.pixelSize: 16
                font.bold: true
                visible: avatarImage.status !== Image.Ready
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
    }

    // Arrow icon on the right
    Item {
        anchors.right: parent.right
        anchors.rightMargin: 12
        anchors.verticalCenter: parent.verticalCenter
        width: 20
        height: 20

        Canvas {
            anchors.fill: parent
            onPaint: {
                var ctx = getContext("2d")
                ctx.reset()
                ctx.strokeStyle = "#8899aa"
                ctx.lineWidth = 2
                ctx.lineCap = "round"
                ctx.lineJoin = "round"
                ctx.beginPath()
                ctx.moveTo(6, 12);
                ctx.lineTo(10, 8);
                ctx.lineTo(14, 12);
                ctx.stroke()
            }
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

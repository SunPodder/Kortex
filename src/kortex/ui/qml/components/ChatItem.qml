import QtQuick
import QtQuick.Controls

Item {
    id: root

    property string chatId: ""
    property string chatTitle: ""
    property string chatPreview: ""
    property bool selected: false

    signal clicked()
    signal deleteClicked()

    implicitHeight: 64

    Rectangle {
        id: itemBackground
        anchors.fill: parent
        anchors.margins: 4
        radius: 8
        color: root.selected ? "#243149" : (mouseArea.containsMouse ? "#1b2230" : "transparent")

        MouseArea {
            id: mouseArea
            anchors.fill: parent
            anchors.rightMargin: 34  // Leave space for delete button
            hoverEnabled: true
            onClicked: root.clicked()
        }
        
        // Separate hover area for the full item (for showing delete button)
        MouseArea {
            id: hoverArea
            anchors.fill: parent
            hoverEnabled: true
            acceptedButtons: Qt.NoButton  // Don't consume clicks
        }

        Column {
            anchors.left: parent.left
            anchors.right: deleteButton.left
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            anchors.margins: 10
            anchors.rightMargin: 4
            spacing: 4
            
            Item {
                width: parent.width
                height: (parent.height - parent.spacing) / 2
                
                Label {
                    anchors.fill: parent
                    text: root.chatTitle
                    color: root.selected ? "#e8edf7" : "#aeb6c6"
                    font.pixelSize: 13
                    font.bold: root.selected
                    elide: Text.ElideRight
                    verticalAlignment: Text.AlignBottom
                }
            }
            
            Item {
                width: parent.width
                height: (parent.height - parent.spacing) / 2
                
                Label {
                    anchors.fill: parent
                    text: root.chatPreview
                    color: "#707a8a"
                    font.pixelSize: 12
                    elide: Text.ElideRight
                    verticalAlignment: Text.AlignTop
                }
            }
        }
        
        // Delete button
        Button {
            id: deleteButton
            anchors.right: parent.right
            anchors.rightMargin: 6
            anchors.verticalCenter: parent.verticalCenter
            width: 28
            height: 28
            visible: hoverArea.containsMouse || root.selected
            flat: true
            text: "✕"
            font.pixelSize: 12
            z: 10  // Ensure button is on top
            
            background: Rectangle {
                color: parent.hovered ? "#3a2020" : "transparent"
                radius: 6
            }
            
            contentItem: Label {
                text: parent.text
                font: parent.font
                color: parent.hovered ? "#f87171" : "#707a8a"
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
            }
            
            onClicked: {
                root.deleteClicked()
            }
            
            ToolTip.visible: hovered
            ToolTip.text: "Delete chat"
            ToolTip.delay: 500
        }
    }
}

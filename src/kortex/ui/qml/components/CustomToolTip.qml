import QtQuick
import QtQuick.Controls
import "../theme"

ToolTip {
    id: control

    Theme { id: theme }

    // Delay before showing tooltip
    delay: 500
    timeout: 3000

    // Custom styling
    contentItem: Label {
        text: control.text
        color: theme.text
        font.pixelSize: 12
        wrapMode: Text.Wrap
    }

    background: Rectangle {
        color: theme.surface2
        border.color: theme.border
        border.width: 1
        radius: 6

        // Subtle shadow
        Rectangle {
            anchors.fill: parent
            anchors.margins: -3
            color: "transparent"
            border.color: "#40000000"
            border.width: 3
            radius: 8
            z: -1
        }
    }

    // Smooth fade in/out
    enter: Transition {
        NumberAnimation { 
            property: "opacity"
            from: 0.0
            to: 1.0
            duration: 150
            easing.type: Easing.OutCubic
        }
    }

    exit: Transition {
        NumberAnimation { 
            property: "opacity"
            from: 1.0
            to: 0.0
            duration: 100
            easing.type: Easing.InCubic
        }
    }
}

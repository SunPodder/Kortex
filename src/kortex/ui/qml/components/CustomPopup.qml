import QtQuick
import QtQuick.Controls
import "../theme"

Popup {
    id: control

    Theme { id: theme }

    // Default properties with custom styling
    modal: true
    focus: true
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
    
    background: Rectangle {
        color: theme.surface
        border.color: theme.border
        border.width: 1
        radius: 12

        // Shadow effect using layers
        Rectangle {
            anchors.fill: parent
            anchors.margins: -8
            color: "transparent"
            border.color: "#30000000"
            border.width: 8
            radius: 16
            z: -1
        }
    }

    // Smooth animations
    enter: Transition {
        NumberAnimation { 
            property: "opacity"
            from: 0.0
            to: 1.0
            duration: 200
            easing.type: Easing.OutCubic
        }
        NumberAnimation { 
            property: "scale"
            from: 0.9
            to: 1.0
            duration: 200
            easing.type: Easing.OutCubic
        }
    }

    exit: Transition {
        NumberAnimation { 
            property: "opacity"
            from: 1.0
            to: 0.0
            duration: 150
            easing.type: Easing.InCubic
        }
        NumberAnimation { 
            property: "scale"
            from: 1.0
            to: 0.95
            duration: 150
            easing.type: Easing.InCubic
        }
    }

    // Overlay dimming effect
    Overlay.modal: Rectangle {
        color: "#80000000"
        
        Behavior on opacity {
            NumberAnimation { duration: 200 }
        }
    }
}

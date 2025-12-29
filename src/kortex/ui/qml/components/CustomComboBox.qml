import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../theme"

ComboBox {
    id: control

    Theme { id: theme }
    padding: 10
    // Custom styling
    background: Rectangle {
        color: control.hovered ? theme.surface2 : theme.surface
        border.color: control.activeFocus ? theme.accent : theme.border
        border.width: 1
        radius: 8

        Behavior on color {
            ColorAnimation { duration: 150 }
        }

        Behavior on border.color {
            ColorAnimation { duration: 150 }
        }
    }

    contentItem: Label {
        leftPadding: 12
        rightPadding: control.indicator.width + 12
        text: control.displayText
        color: theme.text
        font: control.font
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }

    indicator: Item {
        x: control.width - width - 8
        y: control.topPadding + (control.availableHeight - height) / 2
        width: 20
        height: 20

        Canvas {
            anchors.fill: parent
            onPaint: {
                var ctx = getContext("2d")
                ctx.reset()
                ctx.strokeStyle = theme.textMuted
                ctx.lineWidth = 2
                ctx.lineCap = "round"
                ctx.lineJoin = "round"
                ctx.beginPath()
                ctx.moveTo(6, 8)
                ctx.lineTo(10, 12)
                ctx.lineTo(14, 8)
                ctx.stroke()
            }
        }
    }

    // Dropdown popup styling
    popup: Popup {
        y: control.height + 4
        width: control.width
        implicitHeight: contentItem.implicitHeight
        padding: 4

        contentItem: ListView {
            clip: true
            implicitHeight: contentHeight
            model: control.popup.visible ? control.delegateModel : null
            currentIndex: control.highlightedIndex

            ScrollIndicator.vertical: ScrollIndicator { }
        }

        background: Rectangle {
            color: theme.surface
            border.color: theme.border
            border.width: 1
            radius: 8

            // Subtle shadow effect using rectangles
            Rectangle {
                anchors.fill: parent
                anchors.margins: -4
                color: "transparent"
                border.color: "#20000000"
                border.width: 4
                radius: 10
                z: -1
            }
        }

        // Smooth open/close animation
        enter: Transition {
            NumberAnimation { property: "opacity"; from: 0.0; to: 1.0; duration: 150 }
            NumberAnimation { property: "scale"; from: 0.95; to: 1.0; duration: 150; easing.type: Easing.OutCubic }
        }

        exit: Transition {
            NumberAnimation { property: "opacity"; from: 1.0; to: 0.0; duration: 100 }
            NumberAnimation { property: "scale"; from: 1.0; to: 0.95; duration: 100; easing.type: Easing.InCubic }
        }
    }

    // Custom delegate for dropdown items
    delegate: ItemDelegate {
        width: control.width - 8
        height: 36

        contentItem: Label {
            text: control.textRole ? (Array.isArray(control.model) ? modelData[control.textRole] : model[control.textRole]) : modelData
            color: highlighted ? theme.text : theme.textMuted
            font: control.font
            verticalAlignment: Text.AlignVCenter
            leftPadding: 12
        }

        background: Rectangle {
            color: parent.highlighted ? theme.surface2 : "transparent"
            radius: 6

            Behavior on color {
                ColorAnimation { duration: 100 }
            }
        }

        highlighted: control.highlightedIndex === index
    }
}

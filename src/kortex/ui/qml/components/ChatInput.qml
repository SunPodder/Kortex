import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: root
    color: "transparent"

    signal sendMessage(string text)

    // Calculate dynamic height based on text lines
    readonly property int lineHeight: 20
    readonly property int minLines: 1
    readonly property int maxLines: 8
    readonly property int baseHeight: 52
    readonly property int currentLineCount: Math.max(1, Math.min(maxLines, inputField.lineCount))
    readonly property int dynamicHeight: currentLineCount === 1 ? baseHeight : baseHeight + (currentLineCount - 1) * lineHeight

    implicitHeight: dynamicHeight + 30 // Extra space for token count

    ColumnLayout {
        anchors.fill: parent
        anchors.leftMargin: 16
        anchors.rightMargin: 16
        anchors.topMargin: 8
        anchors.bottomMargin: 8
        spacing: 4

        // Main input container - pill shaped
        Rectangle {
            id: inputContainer
            Layout.fillWidth: true
            Layout.preferredHeight: root.dynamicHeight
            color: "#1b2230"
            border.color: inputField.activeFocus ? "#3a68b8" : "#3a4556"
            border.width: 1
            radius: root.currentLineCount === 1 ? height / 2 : 16

            Behavior on radius {
                NumberAnimation { duration: 150; easing.type: Easing.OutQuad }
            }

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 8
                anchors.rightMargin: 8
                anchors.topMargin: root.currentLineCount === 1 ? 0 : 8
                anchors.bottomMargin: root.currentLineCount === 1 ? 0 : 8
                spacing: 4

                // Agent mode toggle button
                Button {
                    id: agentButton
                    Layout.preferredWidth: 36
                    Layout.preferredHeight: 36
                    Layout.alignment: root.currentLineCount === 1 ? Qt.AlignVCenter : Qt.AlignBottom
                    flat: true
                    enabled: ChatController.agentModelsAvailable

                    contentItem: Label {
                        text: "🤖"
                        font.pixelSize: 16
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                        opacity: ChatController.agentModelsAvailable ? 1.0 : 0.5
                    }

                    background: Rectangle {
                        color: ChatController.agentMode ? "#3b82f6" : (parent.hovered && ChatController.agentModelsAvailable ? "#243149" : "transparent")
                        radius: 18
                    }

                    onClicked: ChatController.setAgentMode(!ChatController.agentMode)

                    CustomToolTip {
                        text: {
                            if (!ChatController.agentModelsAvailable) {
                                var missing = ChatController.missingAgentModels
                                return "Agent mode requires: " + missing.join(", ")
                            }
                            return ChatController.agentMode ? "Agent mode (click to disable)" : "Enable agent mode"
                        }
                        visible: parent.hovered
                    }
                }

                // Plus button for tools
                Button {
                    id: plusButton
                    Layout.preferredWidth: 36
                    Layout.preferredHeight: 36
                    Layout.alignment: root.currentLineCount === 1 ? Qt.AlignVCenter : Qt.AlignBottom
                    flat: true

                    contentItem: Label {
                        text: "+"
                        font.pixelSize: 22
                        font.weight: Font.Light
                        color: "#9aa5b8"
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }

                    background: Rectangle {
                        color: parent.hovered ? "#243149" : "transparent"
                        radius: 18
                    }

                    onClicked: toolsPopup.open()

                    CustomToolTip {
                        text: "Tools"
                        visible: parent.hovered && !toolsPopup.visible
                    }
                }

                // Text input area
                ScrollView {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
                    ScrollBar.vertical.policy: root.currentLineCount >= root.maxLines ? ScrollBar.AsNeeded : ScrollBar.AlwaysOff

                    TextArea {
                        id: inputField
                        placeholderText: "Ask anything"
                        wrapMode: TextArea.Wrap
                        color: "#e8edf7"
                        placeholderTextColor: "#707a8a"
                        selectByMouse: true
                        font.pixelSize: 15
                        verticalAlignment: root.currentLineCount === 1 ? TextArea.AlignVCenter : TextArea.AlignTop
                        leftPadding: 4
                        rightPadding: 4
                        topPadding: root.currentLineCount === 1 ? 0 : 4
                        bottomPadding: root.currentLineCount === 1 ? 0 : 4

                        background: Rectangle {
                            color: "transparent"
                        }

                        Keys.onReturnPressed: function(event) {
                            if (event.modifiers === Qt.NoModifier && inputField.text.trim().length > 0) {
                                root.sendMessage(inputField.text)
                                inputField.text = ""
                                event.accepted = true
                            } else if (event.modifiers & Qt.ShiftModifier) {
                                // Allow Shift+Enter for new line
                                event.accepted = false
                            }
                        }
                    }
                }

                // Mic button
                Button {
                    id: micButton
                    Layout.preferredWidth: 36
                    Layout.preferredHeight: 36
                    Layout.alignment: root.currentLineCount === 1 ? Qt.AlignVCenter : Qt.AlignBottom
                    flat: true

                    contentItem: Label {
                        text: "🎤"
                        font.pixelSize: 16
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }

                    background: Rectangle {
                        color: parent.hovered ? "#243149" : "transparent"
                        radius: 18
                    }

                    CustomToolTip {
                        text: "Voice input"
                        visible: parent.hovered
                    }
                }

                // Send button (up arrow when text present)
                Button {
                    id: sendButton
                    Layout.preferredWidth: 36
                    Layout.preferredHeight: 36
                    Layout.alignment: root.currentLineCount === 1 ? Qt.AlignVCenter : Qt.AlignBottom
                    visible: inputField.text.trim().length > 0
                    enabled: inputField.text.trim().length > 0
                    flat: true

                    contentItem: Label {
                        text: "↑"
                        font.pixelSize: 18
                        font.bold: true
                        color: "#ffffff"
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }

                    background: Rectangle {
                        color: parent.down ? "#2a5298" : (parent.hovered ? "#4a7fd8" : "#3a68b8")
                        radius: 18
                    }

                    onClicked: {
                        root.sendMessage(inputField.text)
                        inputField.text = ""
                    }
                }

                // Placeholder circle when no text (matches first image)
                Rectangle {
                    Layout.preferredWidth: 36
                    Layout.preferredHeight: 36
                    Layout.alignment: root.currentLineCount === 1 ? Qt.AlignVCenter : Qt.AlignBottom
                    visible: inputField.text.trim().length === 0
                    color: "transparent"
                    border.color: "#4a5568"
                    border.width: 1.5
                    radius: 18

                    Label {
                        anchors.centerIn: parent
                        text: "↑"
                        font.pixelSize: 16
                        color: "#4a5568"
                    }
                }
            }
        }

        // Token count - subtle, right aligned
        Label {
            text: "Tokens: ~" + Math.floor(inputField.text.length / 4)
            color: "#707a8a"
            font.pixelSize: 11
            Layout.alignment: Qt.AlignRight
            Layout.rightMargin: 8
        }
    }

    // Tools Popup
    Popup {
        id: toolsPopup
        x: plusButton.x + 16
        y: inputContainer.y - height - 8
        width: 180
        padding: 8

        background: Rectangle {
            color: "#1b2230"
            border.color: "#3a4556"
            border.width: 1
            radius: 12
        }

        contentItem: ColumnLayout {
            spacing: 4

            Repeater {
                model: [
                    { icon: "📎", text: "Attach file", action: "attach" },
                    { icon: "🖼️", text: "Add image", action: "image" },
                    { icon: "✏️", text: "Edit mode", action: "edit" }
                ]

                Button {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 40
                    flat: true

                    contentItem: RowLayout {
                        spacing: 12

                        Label {
                            text: modelData.icon
                            font.pixelSize: 16
                        }

                        Label {
                            text: modelData.text
                            color: "#e8edf7"
                            font.pixelSize: 14
                            Layout.fillWidth: true
                        }
                    }

                    background: Rectangle {
                        color: parent.hovered ? "#243149" : "transparent"
                        radius: 8
                    }

                    onClicked: {
                        toolsPopup.close()
                        // Handle action based on modelData.action
                    }
                }
            }
        }
    }
}

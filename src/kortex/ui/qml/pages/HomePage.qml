import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import "../components"

Item {
    id: root

    // Mock chat data
    ListModel {
        id: messagesModel
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        // Chat messages area or empty state
        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            color: "#0f1115"

            // Empty state (centered)
            ColumnLayout {
                anchors.centerIn: parent
                visible: messagesModel.count === 0
                spacing: 24
                width: Math.min(parent.width * 0.6, 700)

                Column {
                    Layout.alignment: Qt.AlignHCenter
                    spacing: 12

                    Label {
                        text: "What's on your mind today?"
                        font.pixelSize: 32
                        font.bold: true
                        color: "#e8edf7"
                        anchors.horizontalCenter: parent.horizontalCenter
                    }

                    Label {
                        text: "Ask anything or start a new conversation"
                        font.pixelSize: 16
                        color: "#9aa5b8"
                        anchors.horizontalCenter: parent.horizontalCenter
                    }
                }

                // Large centered input bar
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 58
                    color: "#1b2230"
                    border.color: "#3a4556"
                    border.width: 1
                    radius: 29

                    RowLayout {
                        anchors.fill: parent
                        anchors.margins: 8
                        spacing: 8

                        Button {
                            Layout.preferredWidth: 40
                            Layout.preferredHeight: 40
                            flat: true
                            text: "+"
                            font.pixelSize: 20

                            background: Rectangle {
                                color: parent.hovered ? "#243149" : "transparent"
                                radius: 20
                            }

                            CustomToolTip {
                                text: "Attach file"
                                visible: parent.hovered
                            }
                        }

                        TextArea {
                            id: emptyInputField
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            placeholderText: "Ask anything..."
                            wrapMode: TextArea.NoWrap
                            color: "#e8edf7"
                            placeholderTextColor: "#707a8a"
                            selectByMouse: true
                            font.pixelSize: 15
                            verticalAlignment: TextArea.AlignVCenter

                            background: Rectangle {
                                color: "transparent"
                            }

                            Keys.onReturnPressed: function(event) {
                                if (event.modifiers === Qt.NoModifier) {
                                    if (emptyInputField.text.trim().length > 0) {
                                        sendEmptyMessage()
                                    }
                                    event.accepted = true
                                }
                            }
                        }

                        Button {
                            Layout.preferredWidth: 40
                            Layout.preferredHeight: 40
                            flat: true
                            text: "🎤"
                            font.pixelSize: 18

                            background: Rectangle {
                                color: parent.hovered ? "#243149" : "transparent"
                                radius: 20
                            }

                            CustomToolTip {
                                text: "Voice input"
                                visible: parent.hovered
                            }
                        }

                        Button {
                            Layout.preferredWidth: 40
                            Layout.preferredHeight: 40
                            enabled: emptyInputField.text.trim().length > 0
                            flat: true
                            text: "➜"
                            font.pixelSize: 20
                            onClicked: sendEmptyMessage()

                            background: Rectangle {
                                color: emptyInputField.text.trim().length > 0 ? "#3a68b8" : "#2a3446"
                                radius: 20
                            }
                        }
                    }
                }

                // Quick actions (optional)
                GridLayout {
                    Layout.alignment: Qt.AlignHCenter
                    columns: 3
                    columnSpacing: 12
                    rowSpacing: 12

                    Repeater {
                        model: [
                            {icon: "💡", text: "Give me ideas"},
                            {icon: "✍️", text: "Help me write"},
                            {icon: "🔍", text: "Analyze data"}
                        ]

                        Button {
                            Layout.preferredWidth: 160
                            Layout.preferredHeight: 44
                            text: modelData.icon + " " + modelData.text
                            flat: true

                            background: Rectangle {
                                color: parent.hovered ? "#1b2230" : "transparent"
                                border.color: "#3a4556"
                                border.width: 1
                                radius: 8
                            }

                            contentItem: Label {
                                text: parent.text
                                color: "#9aa5b8"
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                                font.pixelSize: 13
                            }

                            onClicked: {
                                emptyInputField.text = modelData.text.replace(modelData.icon + " ", "")
                                sendEmptyMessage()
                            }
                        }
                    }
                }
            }

            // Chat messages view (when conversation active)
            ListView {
                id: chatView
                anchors.fill: parent
                anchors.margins: 20
                spacing: 12
                clip: true
                visible: messagesModel.count > 0

                model: messagesModel

                delegate: MessageBubble {
                    width: chatView.width - 40
                    text: model.text
                    isUser: model.isUser
                }

                onCountChanged: {
                    Qt.callLater(() => chatView.positionViewAtEnd())
                }
            }
        }

        // Input area (when conversation active)
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 140
            color: "#151a22"
            border.color: "#2a3446"
            border.width: 1
            visible: messagesModel.count > 0

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 12
                spacing: 8

                // Tools bar
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8

                    Button {
                        text: "📎"
                        flat: true

                        CustomToolTip {
                            text: "Attach file"
                            visible: parent.hovered
                        }
                    }

                    Button {
                        text: "🖼️"
                        flat: true

                        CustomToolTip {
                            text: "Add image"
                            visible: parent.hovered
                        }
                    }

                    Button {
                        text: "🎤"
                        flat: true

                        CustomToolTip {
                            text: "Voice input"
                            visible: parent.hovered
                        }
                    }

                    Item { Layout.fillWidth: true }

                    Label {
                        text: "Tokens: ~" + (conversationInputField.text.length / 4).toFixed(0)
                        color: "#707a8a"
                        font.pixelSize: 11
                    }
                }

                // Input area
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8

                    ScrollView {
                        Layout.fillWidth: true
                        Layout.preferredHeight: Math.min(conversationInputField.implicitHeight, 80)

                        TextArea {
                            id: conversationInputField
                            placeholderText: "Message Kortex..."
                            wrapMode: TextArea.Wrap
                            color: "#e8edf7"
                            placeholderTextColor: "#707a8a"
                            selectByMouse: true
                            font.pixelSize: 14

                            background: Rectangle {
                                color: "transparent"
                            }

                            Keys.onReturnPressed: function(event) {
                                if (event.modifiers & Qt.ControlModifier) {
                                    sendConversationMessage()
                                    event.accepted = true
                                }
                            }
                        }
                    }

                    Button {
                        text: "Send"
                        enabled: conversationInputField.text.trim().length > 0
                        font.bold: true
                        
                        contentItem: Label {
                            text: parent.text
                            font: parent.font
                            color: parent.enabled ? "#ffffff" : "#707a8a"
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                        }

                        background: Rectangle {
                            color: parent.enabled ? (parent.down ? "#2a4c8a" : (parent.hovered ? "#3a68b8" : "#325ab0")) : "#1b2230"
                            border.color: parent.enabled ? "transparent" : "#2a3446"
                            border.width: 1
                            radius: 8
                        }
                        
                        onClicked: sendConversationMessage()
                    }
                }

                Label {
                    text: "Ctrl+Enter to send"
                    color: "#707a8a"
                    font.pixelSize: 10
                    Layout.alignment: Qt.AlignRight
                }
            }
        }
    }

    function sendEmptyMessage() {
        if (emptyInputField.text.trim().length === 0) return

        messagesModel.append({
            text: emptyInputField.text,
            isUser: true
        })

        emptyInputField.text = ""

        // Mock AI response
        Qt.callLater(() => {
            messagesModel.append({
                text: "I'm processing your request. AI functionality will be implemented soon!",
                isUser: false
            })
        })
    }

    function sendConversationMessage() {
        if (conversationInputField.text.trim().length === 0) return

        messagesModel.append({
            text: conversationInputField.text,
            isUser: true
        })

        conversationInputField.text = ""

        // Mock AI response
        Qt.callLater(() => {
            messagesModel.append({
                text: "I received your message. AI response functionality will be implemented soon!",
                isUser: false
            })
        })
    }
}

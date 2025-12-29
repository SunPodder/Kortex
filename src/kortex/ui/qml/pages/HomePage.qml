import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import "../components" as Components

Item {
    id: root

    property string currentChatId: ""
    property var pendingToolCalls: []
    
    signal chatCreated(string chatId)

    // Messages model
    ListModel {
        id: messagesModel
    }

    // Load messages when chat changes
    onCurrentChatIdChanged: {
        loadMessages()
        pendingToolCalls = []
    }

    function loadMessages() {
        messagesModel.clear()
        if (currentChatId) {
            var messages = ChatController.getMessages(currentChatId)
            for (var i = 0; i < messages.length; i++) {
                messagesModel.append(messages[i])
            }
        }
    }

    // Connect to backend signals
    Connections {
        target: ChatController
        
        function onMessagesChanged() {
            loadMessages()
        }
        
        function onIsLoadingChanged() {
            // Could show loading indicator
        }
        
        function onToolCallsPending(chatId, toolCalls) {
            if (chatId === root.currentChatId) {
                root.pendingToolCalls = toolCalls
            }
        }
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

                        // Agent mode toggle button
                        Button {
                            Layout.preferredWidth: 40
                            Layout.preferredHeight: 40
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
                                radius: 20
                            }

                            onClicked: ChatController.setAgentMode(!ChatController.agentMode)

                            Components.CustomToolTip {
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

                            Components.CustomToolTip {
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

                            Components.CustomToolTip {
                                text: "Voice input"
                                visible: parent.hovered
                            }
                        }

                        Button {
                            Layout.preferredWidth: 40
                            Layout.preferredHeight: 40
                            enabled: emptyInputField.text.trim().length > 0 && !ChatController.isLoading
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
                anchors.bottomMargin: permissionCard.visible ? permissionCard.height + 30 : 20
                spacing: 12
                clip: true
                visible: messagesModel.count > 0

                model: messagesModel

                delegate: Components.MessageBubble {
                    width: chatView.width - 40
                    text: model.content
                    isUser: model.isUser
                }

                onCountChanged: {
                    Qt.callLater(() => chatView.positionViewAtEnd())
                }
            }
            
            // Tool Permission Card
            Components.ToolPermissionCard {
                id: permissionCard
                anchors.bottom: parent.bottom
                anchors.horizontalCenter: parent.horizontalCenter
                anchors.bottomMargin: 16
                width: Math.min(parent.width - 32, 500)
                toolCalls: root.pendingToolCalls
                chatId: root.currentChatId
                visible: root.pendingToolCalls.length > 0
                
                onApproved: function(approvedIds, deniedIds) {
                    ChatController.respondToToolCalls(root.currentChatId, approvedIds, deniedIds)
                    root.pendingToolCalls = []
                }
            }
            
            // Loading indicator
            Rectangle {
                anchors.bottom: permissionCard.visible ? permissionCard.top : parent.bottom
                anchors.horizontalCenter: parent.horizontalCenter
                anchors.bottomMargin: 20
                width: loadingRow.width + 24
                height: 40
                radius: 20
                color: "#1b2230"
                visible: ChatController.isLoading
                
                Row {
                    id: loadingRow
                    anchors.centerIn: parent
                    spacing: 8
                    
                    BusyIndicator {
                        width: 20
                        height: 20
                        running: ChatController.isLoading
                    }
                    
                    Label {
                        text: "Thinking..."
                        color: "#9aa5b8"
                        font.pixelSize: 13
                        anchors.verticalCenter: parent.verticalCenter
                    }
                }
            }
        }

        // Input area (when conversation active)
        Components.ChatInput {
            id: chatInputArea
            Layout.fillWidth: true
            Layout.preferredHeight: implicitHeight
            visible: messagesModel.count > 0
            
            onSendMessage: function(text) {
                if (text.trim().length === 0) return
                if (ChatController.isLoading) return
                ChatController.sendMessage(currentChatId, text)
            }
        }
    }

    function sendEmptyMessage() {
        if (emptyInputField.text.trim().length === 0) return
        if (ChatController.isLoading) return

        var message = emptyInputField.text
        emptyInputField.text = ""

        // Create new chat if needed, then send message
        if (!currentChatId) {
            var newChatId = ChatController.createChat()
            root.chatCreated(newChatId)
            ChatController.sendMessage(newChatId, message)
        } else {
            ChatController.sendMessage(currentChatId, message)
        }
    }
}

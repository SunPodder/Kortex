import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Qt.labs.settings as Labs

import "theme"
import "components"
import "pages"

ApplicationWindow {
    id: window
    width: 1280
    height: 760
    minimumWidth: 1000
    minimumHeight: 600
    visible: true
    title: "Kortex"

    Theme { id: theme }

    Labs.Settings {
        id: appSettings
        category: "app"
    }

    property string currentChatId: ""
    property var availableModels: []
    property int selectedModelIndex: 0
    property bool sidebarCollapsed: false

    // Chat list model
    ListModel {
        id: chatsModel
    }

    // Load chats from backend
    function loadChats() {
        chatsModel.clear()
        var chats = ChatController.getChats()
        if (chats && chats.length > 0) {
            for (var i = 0; i < chats.length; i++) {
                var chat = chats[i]
                if (chat) {
                    chatsModel.append({
                        "id": chat.id || "",
                        "title": chat.title || "New Chat",
                        "preview": chat.preview || "",
                        "model": chat.model || ""
                    })
                }
            }
        }
        
        // Select first chat if available and none selected
        if (chatsModel.count > 0 && !window.currentChatId) {
            var firstChat = chatsModel.get(0)
            if (firstChat && firstChat.id) {
                window.currentChatId = firstChat.id
                ChatController.selectChat(window.currentChatId)
            }
        }
    }

    // Load models from backend
    function loadModels() {
        window.availableModels = ChatController.getModels()
        if (window.availableModels.length > 0) {
            // Find current model index
            var currentModel = ChatController.currentModel
            for (var i = 0; i < window.availableModels.length; i++) {
                if (window.availableModels[i] === currentModel) {
                    window.selectedModelIndex = i
                    break
                }
            }
        }
    }

    // Create new chat
    function createNewChat() {
        var chatId = ChatController.createChat()
        window.currentChatId = chatId
        loadChats()
    }

    // Delete a chat
    function deleteChat(chatId) {
        if (!chatId) return
        
        ChatController.deleteChat(chatId)
        loadChats()
        
        // Update current chat ID
        if (chatsModel.count > 0) {
            var firstChat = chatsModel.get(0)
            if (firstChat && firstChat.id) {
                window.currentChatId = firstChat.id
                ChatController.selectChat(window.currentChatId)
            } else {
                window.currentChatId = ""
            }
        } else {
            window.currentChatId = ""
        }
    }

    // Select a chat
    function selectChat(chatId) {
        window.currentChatId = chatId || ""
        ChatController.selectChat(chatId || "")
    }

    // Initialize on component completion
    Component.onCompleted: {
        loadModels()
        loadChats()
    }

    // Connect to backend signals
    Connections {
        target: ChatController
        
        function onChatsChanged() {
            loadChats()
        }
        
        function onModelsChanged() {
            loadModels()
        }
        
        function onCurrentChatChanged() {
            window.currentChatId = ChatController.currentChatId || ""
        }
    }

    // Auto-hide to tray on close
    onClosing: function(close) {
        close.accepted = false
        window.visible = false
    }

    Rectangle {
        anchors.fill: parent
        color: theme.bg

        RowLayout {
            anchors.fill: parent
            spacing: 0

            Rectangle {
                id: sidebar
                Layout.preferredWidth: 260
                Layout.fillHeight: true
                color: theme.surface
                border.color: theme.border
                border.width: 1

                Behavior on Layout.preferredWidth {
                    NumberAnimation { duration: 200; easing.type: Easing.InOutQuad }
                }

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 8
                    spacing: 4

                    // App Title
                    Label {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 40
                        text: "Kortex"
                        font.pixelSize: 20
                        font.bold: true
                        color: theme.text
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        height: 1
                        color: theme.border
                        opacity: 0.5
                    }

                    // New Chat button
                    SidebarItem {
                        Layout.fillWidth: true
                        icon: "+"
                        text: window.sidebarCollapsed ? "" : "New chat"
                        onClicked: createNewChat()
                    }

                    // Section items
                    SidebarItem {
                        Layout.fillWidth: true
                        visible: !window.sidebarCollapsed
                        icon: "🔍"
                        text: "Search chats"
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        height: 1
                        color: theme.border
                        opacity: 0.5
                        visible: !window.sidebarCollapsed
                    }

                    // Your chats section
                    Label {
                        Layout.fillWidth: true
                        text: "Your chats"
                        color: theme.textMuted
                        font.pixelSize: 12
                        font.bold: true
                        leftPadding: 10
                        visible: !window.sidebarCollapsed
                    }

                    // Chat list
                    ScrollView {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        clip: true
                        visible: !window.sidebarCollapsed

                        ListView {
                            id: chatListView
                            model: chatsModel
                            spacing: 2

                            delegate: ChatItem {
                                required property int index
                                required property string id
                                required property string title
                                required property string preview
                                
                                width: chatListView.width
                                chatId: id
                                chatTitle: title
                                chatPreview: preview
                                selected: id === window.currentChatId
                                onClicked: {
                                    selectChat(id)
                                }
                                onDeleteClicked: {
                                    deleteChat(id)
                                }
                            }
                        }
                    }

                    // Spacer
                    Item {
                        Layout.fillWidth: true
                        Layout.fillHeight: window.sidebarCollapsed
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        height: 1
                        color: theme.border
                        opacity: 0.5
                        visible: !window.sidebarCollapsed
                    }

                    // User profile
                    UserProfileCard {
                        Layout.fillWidth: true
                        visible: !window.sidebarCollapsed
                        onSettingsClicked: settingsPopup.open()
                    }
                }
            }

            // Main content area
            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                color: theme.bg

                ColumnLayout {
                    anchors.fill: parent
                    spacing: 0

                    // Top navigation bar
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 56
                        color: theme.surface
                        border.color: theme.border
                        border.width: 1

                        RowLayout {
                            anchors.fill: parent
                            anchors.margins: 12
                            spacing: 12

                            // Model selector
                            CustomComboBox {
                                id: modelSelector
                                Layout.preferredWidth: 200
                                Layout.leftMargin: 8
                                model: window.availableModels.length > 0 ? window.availableModels : ["No models available"]
                                currentIndex: window.selectedModelIndex
                                enabled: window.availableModels.length > 0
                                
                                onCurrentIndexChanged: {
                                    if (window.availableModels.length > 0 && currentIndex >= 0) {
                                        ChatController.setModel(window.availableModels[currentIndex])
                                    }
                                }
                            }

                            // Refresh models button
                            Button {
                                text: "↻"
                                font.pixelSize: 16
                                implicitWidth: 36
                                implicitHeight: 36
                                
                                background: Rectangle {
                                    color: parent.down ? "#2a4c8a" : (parent.hovered ? "#3a68b8" : "transparent")
                                    radius: 8
                                    border.color: theme.border
                                    border.width: 1
                                }
                                
                                contentItem: Label {
                                    text: parent.text
                                    font: parent.font
                                    color: theme.text
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                }
                                
                                onClicked: {
                                    ChatController.refreshModels()
                                    loadModels()
                                }
                                
                                CustomToolTip {
                                    text: "Refresh models"
                                    visible: parent.hovered
                                }
                            }

                            // Ollama status indicator
                            Rectangle {
                                width: 10
                                height: 10
                                radius: 5
                                color: ChatController.isOllamaAvailable() ? "#4ade80" : "#f87171"
                                
                                CustomToolTip {
                                    text: ChatController.isOllamaAvailable() ? "Ollama is running" : "Ollama is not running"
                                    visible: parent.children[0].containsMouse
                                }
                                
                                MouseArea {
                                    anchors.fill: parent
                                    hoverEnabled: true
                                }
                            }

                            Item { Layout.fillWidth: true }

                            // New Chat button
                            Button {
                                text: "+ New Chat"
                                font.bold: true
                                padding: 8
                                
                                contentItem: Label {
                                    text: parent.text
                                    font: parent.font
                                    color: "#ffffff"
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                }

                                background: Rectangle {
                                    color: parent.down ? "#2a4c8a" : (parent.hovered ? "#3a68b8" : "#325ab0")
                                    radius: 8
                                }

                                onClicked: createNewChat()
                            }
                        }
                    }

                    // Chat area
                    HomePage { 
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        currentChatId: window.currentChatId
                        
                        onChatCreated: function(chatId) {
                            window.currentChatId = chatId
                            loadChats()
                        }
                    }
                }
            }
        }
    }

    // Settings dialog
    CustomPopup {
        id: settingsPopup
        anchors.centerIn: parent
        width: 600
        height: 500

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 20
            spacing: 12

            RowLayout {
                Layout.fillWidth: true

                Label {
                    text: "Settings"
                    font.pixelSize: 22
                    font.bold: true
                    color: theme.text
                    Layout.fillWidth: true
                }

                Button {
                    text: "✕"
                    flat: true
                    onClicked: settingsPopup.close()
                }
            }

            Rectangle {
                Layout.fillWidth: true
                height: 1
                color: theme.border
            }

            ScrollView {
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true

                SettingsPage { }
            }
        }
    }
}

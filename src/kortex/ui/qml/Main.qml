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

    property int currentChatIndex: 0
    property bool sidebarCollapsed: false

    // Mock chat list
    ListModel {
        id: chatsModel
        ListElement {
            title: "New conversation"
            preview: "Hello! I'm Kortex..."
        }
        ListElement {
            title: "Python debugging help"
            preview: "Can you help me fix..."
        }
        ListElement {
            title: "Project ideas"
            preview: "I need some ideas for..."
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

            // Collapsible Sidebar
            Rectangle {
                id: sidebar
                Layout.preferredWidth: window.sidebarCollapsed ? 60 : 260
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

                    // Collapse toggle button
                    Button {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 40
                        flat: true
                        text: window.sidebarCollapsed ? "☰" : "☰"
                        font.pixelSize: 18
                        onClicked: window.sidebarCollapsed = !window.sidebarCollapsed

                        CustomToolTip {
                            text: window.sidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"
                            visible: parent.hovered
                        }
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
                        onClicked: {
                            chatsModel.insert(0, {
                                title: "New conversation",
                                preview: "Start chatting..."
                            })
                            window.currentChatIndex = 0
                        }
                    }

                    // Section items
                    SidebarItem {
                        Layout.fillWidth: true
                        visible: !window.sidebarCollapsed
                        icon: "🔍"
                        text: "Search chats"
                    }

                    SidebarItem {
                        Layout.fillWidth: true
                        visible: !window.sidebarCollapsed
                        icon: "🖼️"
                        text: "Images"
                        badge: "NEW"
                    }

                    SidebarItem {
                        Layout.fillWidth: true
                        visible: !window.sidebarCollapsed
                        icon: "🧩"
                        text: "Apps"
                    }

                    SidebarItem {
                        Layout.fillWidth: true
                        visible: !window.sidebarCollapsed
                        icon: "📁"
                        text: "Projects"
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
                                width: chatListView.width
                                title: model.title
                                preview: model.preview
                                selected: index === window.currentChatIndex
                                onClicked: window.currentChatIndex = index
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
                                model: ["GPT-4 Turbo", "Claude 3.5 Sonnet", "Llama 3", "Local Model"]
                                currentIndex: 0
                            }

                            Item { Layout.fillWidth: true }

                            // New Chat button
                            Button {
                                text: "+ New Chat"
                                highlighted: true
                                onClicked: {
                                    chatsModel.insert(0, {
                                        title: "New conversation",
                                        preview: "Start chatting..."
                                    })
                                    window.currentChatIndex = 0
                                }
                            }
                        }
                    }

                    // Chat area
                    HomePage { 
                        Layout.fillWidth: true
                        Layout.fillHeight: true
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

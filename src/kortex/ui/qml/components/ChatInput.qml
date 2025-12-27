import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: root
    color: "#151a22"
    border.color: "#2a3446"
    border.width: 1

    signal sendMessage(string text)

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 12
        spacing: 8

        // Model and tools bar
        RowLayout {
            Layout.fillWidth: true
            spacing: 8

            ComboBox {
                id: modelCombo
                Layout.preferredWidth: 180
                model: ["GPT-4", "Claude 3.5", "Llama 3", "Local Model"]
                currentIndex: 0
            }

            Rectangle {
                width: 1
                Layout.fillHeight: true
                color: "#2a3446"
            }

            Button {
                text: "📎"
                flat: true
                ToolTip.text: "Attach file"
                ToolTip.visible: hovered
            }

            Button {
                text: "🖼️"
                flat: true
                ToolTip.text: "Add image"
                ToolTip.visible: hovered
            }

            Button {
                text: "🎤"
                flat: true
                ToolTip.text: "Voice input"
                ToolTip.visible: hovered
            }

            Item { Layout.fillWidth: true }

            Label {
                text: "Tokens: 0"
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
                Layout.preferredHeight: Math.min(inputField.implicitHeight, 120)

                TextArea {
                    id: inputField
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
                            root.sendMessage(inputField.text)
                            inputField.text = ""
                            event.accepted = true
                        }
                    }
                }
            }

            Button {
                text: "Send"
                enabled: inputField.text.trim().length > 0
                highlighted: true
                onClicked: {
                    root.sendMessage(inputField.text)
                    inputField.text = ""
                }
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

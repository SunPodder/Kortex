import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: root
    
    property var toolCalls: []
    property string chatId: ""
    
    signal approved(var approvedIds, var deniedIds)
    signal dismissed()
    
    visible: toolCalls.length > 0
    color: "#1b2230"
    border.color: "#f59e0b"
    border.width: 2
    radius: 12
    
    implicitHeight: contentColumn.height + 32
    implicitWidth: parent ? Math.min(parent.width - 32, 500) : 500
    
    ColumnLayout {
        id: contentColumn
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.margins: 16
        spacing: 12
        
        // Header
        RowLayout {
            Layout.fillWidth: true
            spacing: 8
            
            Label {
                text: "⚠️"
                font.pixelSize: 20
            }
            
            Label {
                text: "Permission Required"
                font.pixelSize: 16
                font.bold: true
                color: "#f59e0b"
                Layout.fillWidth: true
            }
        }
        
        Label {
            Layout.fillWidth: true
            text: "The AI wants to perform the following action" + (root.toolCalls.length > 1 ? "s" : "") + ":"
            color: "#9aa5b8"
            font.pixelSize: 13
            wrapMode: Text.WordWrap
        }
        
        // Tool calls list
        Repeater {
            model: root.toolCalls
            
            delegate: Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: toolColumn.height + 16
                color: "#243149"
                radius: 8
                border.color: "#3a4556"
                border.width: 1
                
                property var toolData: modelData
                property bool isApproved: true
                
                ColumnLayout {
                    id: toolColumn
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: parent.top
                    anchors.margins: 8
                    spacing: 6
                    
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 8
                        
                        Label {
                            text: getToolIcon(toolData.tool_name)
                            font.pixelSize: 16
                        }
                        
                        Label {
                            text: toolData.tool_name
                            font.bold: true
                            color: "#e8edf7"
                            font.pixelSize: 14
                        }
                        
                        Item { Layout.fillWidth: true }
                        
                        // Permission badges
                        Repeater {
                            model: toolData.permission_names || []
                            
                            Rectangle {
                                height: 20
                                width: permLabel.width + 12
                                radius: 4
                                color: getPermissionColor(modelData)
                                
                                Label {
                                    id: permLabel
                                    anchors.centerIn: parent
                                    text: modelData
                                    font.pixelSize: 10
                                    color: "#ffffff"
                                }
                            }
                        }
                    }
                    
                    Label {
                        Layout.fillWidth: true
                        text: toolData.tool_description
                        color: "#9aa5b8"
                        font.pixelSize: 12
                        wrapMode: Text.WordWrap
                    }
                    
                    // Show arguments
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: argsText.height + 12
                        color: "#0f1115"
                        radius: 4
                        visible: Object.keys(toolData.arguments || {}).length > 0
                        
                        Label {
                            id: argsText
                            anchors.left: parent.left
                            anchors.right: parent.right
                            anchors.top: parent.top
                            anchors.margins: 6
                            text: formatArguments(toolData.arguments)
                            color: "#7dd3fc"
                            font.family: "monospace"
                            font.pixelSize: 11
                            wrapMode: Text.WrapAnywhere
                        }
                    }
                }
            }
        }
        
        // Action buttons
        RowLayout {
            Layout.fillWidth: true
            Layout.topMargin: 8
            spacing: 12
            
            Button {
                Layout.fillWidth: true
                text: "Deny All"
                
                background: Rectangle {
                    color: parent.down ? "#7f1d1d" : (parent.hovered ? "#991b1b" : "#450a0a")
                    radius: 8
                    border.color: "#dc2626"
                    border.width: 1
                }
                
                contentItem: Label {
                    text: parent.text
                    color: "#fca5a5"
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                    font.pixelSize: 13
                }
                
                onClicked: {
                    var deniedIds = root.toolCalls.map(function(tc) { return tc.call_id; });
                    root.approved([], deniedIds);
                }
            }
            
            Button {
                Layout.fillWidth: true
                text: "Allow All"
                
                background: Rectangle {
                    color: parent.down ? "#14532d" : (parent.hovered ? "#166534" : "#052e16")
                    radius: 8
                    border.color: "#22c55e"
                    border.width: 1
                }
                
                contentItem: Label {
                    text: parent.text
                    color: "#86efac"
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                    font.pixelSize: 13
                    font.bold: true
                }
                
                onClicked: {
                    var approvedIds = root.toolCalls.map(function(tc) { return tc.call_id; });
                    root.approved(approvedIds, []);
                }
            }
        }
    }
    
    function getToolIcon(toolName) {
        switch(toolName) {
            case "read_dir": return "📁";
            case "read_file": return "📄";
            case "write_file": return "✏️";
            case "run_cmd": return "⚡";
            default: return "🔧";
        }
    }
    
    function getPermissionColor(permName) {
        switch(permName) {
            case "Read Files": return "#3b82f6";
            case "Write Files": return "#f59e0b";
            case "Run Commands": return "#ef4444";
            case "Internet Access": return "#8b5cf6";
            default: return "#6b7280";
        }
    }
    
    function formatArguments(args) {
        if (!args) return "";
        var parts = [];
        for (var key in args) {
            var value = args[key];
            if (typeof value === "string" && value.length > 100) {
                value = value.substring(0, 100) + "...";
            }
            parts.push(key + ": " + JSON.stringify(value));
        }
        return parts.join("\n");
    }
}

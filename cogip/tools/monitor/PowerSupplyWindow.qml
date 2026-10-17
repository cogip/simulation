pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window

Window {
    id: powerSupplyWindow

    property var emergencyStopEngaged: null
    readonly property var rails: [
        {
            key: "p3V3",
            label: "3.3V"
        },
        {
            key: "p5V0",
            label: "5.0V"
        },
        {
            key: "p7V5",
            label: "7.5V"
        },
        {
            key: "pxVx",
            label: "Variable"
        },
        {
            key: "p12V0",
            label: "12V"
        }
    ]
    // Last power supply states, named after the events that carry them (missing or null if unknown)
    property var states: ({})

    function pgood(rail) {
        // 12V rail has no power good signal, always shown as OK
        return rail === "p12V0" ? true : state("power_rails_status", rail + "_pgood");
    }

    function state(name, field) {
        const value = states[name];
        return value ? value[field] : null;
    }

    color: "#2b2b2b"
    height: contentLayout.implicitHeight + 32
    minimumHeight: contentLayout.implicitHeight + 32
    minimumWidth: contentLayout.implicitWidth + 32
    modality: Qt.NonModal
    palette.text: "#ffffff"
    palette.window: "#2a2a2a"
    palette.windowText: "#ffffff"
    title: "Power Supply"
    width: contentLayout.implicitWidth + 32

    RowLayout {
        id: contentLayout

        anchors.fill: parent
        anchors.margins: 16
        spacing: 32

        ColumnLayout {
            Layout.alignment: Qt.AlignTop
            spacing: 8

            HeaderLabel {
                font.pixelSize: 16
                text: "Status"
            }

            GridLayout {
                columnSpacing: 16
                columns: 2
                rowSpacing: 8

                Label {
                    color: "white"
                    text: "Emergency stop"
                }

                StateCell {
                    readonly property var released: typeof powerSupplyWindow.emergencyStopEngaged === "boolean" ? !powerSupplyWindow.emergencyStopEngaged : null

                    ok: released
                    text: released ? "Released" : "Engaged"
                }

                Label {
                    color: "white"
                    text: "Battery"
                }

                StateCell {
                    ok: powerSupplyWindow.state("power_source_status", "battery_valid")
                    text: ok ? "Connected" : "Disconnected"
                }

                Label {
                    color: "white"
                    text: "DC supply"
                }

                StateCell {
                    ok: powerSupplyWindow.state("power_source_status", "dc_supply_valid")
                    text: ok ? "Connected" : "Disconnected"
                }
            }
        }

        ColumnLayout {
            Layout.alignment: Qt.AlignTop
            spacing: 8

            HeaderLabel {
                font.pixelSize: 16
                text: "Rails"
            }

            // Filled column by column: a header followed by one cell per rail
            GridLayout {
                columnSpacing: 16
                flow: GridLayout.TopToBottom
                rowSpacing: 8
                rows: powerSupplyWindow.rails.length + 1

                HeaderLabel {
                    text: "Rail"
                }

                Repeater {
                    model: powerSupplyWindow.rails

                    Label {
                        required property var modelData

                        color: "white"
                        text: modelData.label
                    }
                }

                HeaderLabel {
                    text: "Power good"
                }

                Repeater {
                    model: powerSupplyWindow.rails

                    StateCell {
                        required property var modelData

                        ok: powerSupplyWindow.pgood(modelData.key)
                        text: ok ? "OK" : "Fault"
                    }
                }

                HeaderLabel {
                    text: "Voltage (V)"
                }

                Repeater {
                    model: powerSupplyWindow.rails

                    Label {
                        readonly property var measure: powerSupplyWindow.state("power_rails_measures", modelData.key)
                        required property var modelData

                        color: "white"
                        text: measure ? (measure.voltage_mv / 1000).toFixed(2) : "—"
                    }
                }

                HeaderLabel {
                    text: "Current (mA)"
                }

                Repeater {
                    model: powerSupplyWindow.rails

                    Label {
                        readonly property var measure: powerSupplyWindow.state("power_rails_measures", modelData.key)
                        required property var modelData

                        color: "white"
                        text: measure ? measure.current_ma.toFixed(0) : "—"
                    }
                }

                HeaderLabel {
                    text: "Power (W)"
                }

                Repeater {
                    model: powerSupplyWindow.rails

                    Label {
                        readonly property var measure: powerSupplyWindow.state("power_rails_measures", modelData.key)
                        required property var modelData

                        color: "white"
                        text: measure ? (measure.voltage_mv * measure.current_ma / 1e6).toFixed(2) : "—"
                    }
                }
            }
        }
    }

    component HeaderLabel: Label {
        color: "white"
        font.bold: true
    }

    // Colored dot followed by a text: green if ok, red if not, only "—" if the state is unknown (null).
    // Inline components do not share the id scope of the window, so only use their own properties.
    component StateCell: RowLayout {
        id: stateCell

        property var ok: null
        property string text: ""

        spacing: 6

        Rectangle {
            Layout.preferredHeight: 12
            Layout.preferredWidth: 12
            color: stateCell.ok ? "#27ae60" : "#c0392b"
            radius: 6
            visible: typeof stateCell.ok === "boolean"
        }

        Label {
            color: "white"
            text: typeof stateCell.ok === "boolean" ? stateCell.text : "—"
        }
    }
}

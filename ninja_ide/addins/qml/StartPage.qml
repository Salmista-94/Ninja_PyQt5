import QtQuick 2.4
import QtQuick.Layouts 1.2

Rectangle {
    id: root

    property int _padding: (mainArea.width / 4)
    property bool compressed: true

    signal markAsFavorite(string pat, bool value)
    signal openProject(string path)
    signal removeProject(string path)
    signal openPreferences
    width: 630
    height: 400
    
    gradient: Gradient {
        GradientStop { position: 0.0; color: "#ffffff" }
         GradientStop { position: 1.0; color: "#a4a4a4" }
     }

    onWidthChanged: {
        if(root.width < 500){
            compressed = true;
            root._padding = (mainArea.width / 2);
            logo.width = 300;
            txtProjects.visible = false;
            projectList.visible = false;
        }else{
            compressed = false;
            root._padding = (mainArea.width / 4);
            logo.width = logo.sourceSize.width;
            txtProjects.visible = true;
            projectList.visible = true;
        }
    }

    Rectangle {
        id: mainArea
        color: "white"
        anchors.fill: parent
        radius: 10
        anchors.margins: parent.height / 14
        smooth: true
        Image {
            id: logo
            antialiasing: true
            source: "img/ninja-ide.png"
            anchors.left: parent.left
            anchors.top: parent.top
            anchors.leftMargin: 10
            anchors.topMargin: 10
            fillMode: Image.PreserveAspectFit
        }
        Text {
            id: txtWelcome
            x: 0
            y: 49
            width: parent.width
            height: 60
            color: "#2f2d2d"
            text: qsTr("Welcome!")
            anchors.verticalCenterOffset: -25
            anchors.verticalCenter: parent.verticalCenter
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            anchors.left: logo.left
            anchors.leftMargin: 0
            anchors.right: projectList.left
            anchors.rightMargin: 20
            font.bold: true
            font.pointSize: 45
            style: Text.Raised
            styleColor: "black"
        }

        Text {
            id: txtDescription
            text: qsTr("NINJA-IDE (from: \"Ninja-IDE Is Not Just Another IDE\"), is a cross-platform integrated development environment specially designed to build Python Applications. NINJA-IDE provides tools to simplify the Python-software development and handles all kinds of situations thanks to its rich extensibility.")
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignBottom
            anchors.top: txtWelcome.bottom
            anchors.topMargin: 30
            anchors.left: txtWelcome.left
            anchors.leftMargin: 0
            anchors.right: txtWelcome.right
            anchors.rightMargin: 0
            wrapMode: Text.WordWrap
        }


        Rectangle {
            id: colButtons
            y: 334
            height: 35
            anchors.left: logo.left
            anchors.leftMargin: 0
            anchors.right: txtWelcome.right
            anchors.rightMargin: 0
            anchors.bottom: parent.bottom
            anchors.bottomMargin: 15
            Row {
                anchors.fill: parent
                spacing: 10
                Button {
                    width: (colButtons.width - parent.spacing)/2
                    height: colButtons.height
                    text: qsTr("Chat with us!")
                    onClicked: Qt.openUrlExternally("https://kiwiirc.com/client/chat.freenode.net/?nick=Ninja|?&theme=cli#ninja-ide")
                }
                Button {
                    width: (colButtons.width - parent.spacing)/2
                    height: colButtons.height
                    text: qsTr("Preferences")
                    onClicked: openPreferences();
                }
            }
        }

        Text {
            id: txtProjects
            width: 150
            height: 30
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.topMargin: 30
            color: "#2f2d2d"
            text: qsTr("Recent Projects:")
            verticalAlignment: Text.AlignVCenter
            horizontalAlignment: Text.AlignLeft
            wrapMode: Text.NoWrap
            anchors.left: projectList.left
            anchors.leftMargin: 0
            anchors.rightMargin: 5
            font.bold: true
            font.pointSize: Math.max(width/15, 8)
            style: Text.Raised
            styleColor: "black"
        }

        ProjectList {
            id: projectList
            anchors.bottom: colButtons.bottom
            anchors.bottomMargin: 0
            Layout.minimumWidth: 225
            width: parent.width/2.5
            anchors.rightMargin: 5
            anchors.right: parent.right
            anchors.top: txtProjects.bottom
            anchors.topMargin: 10

            onMarkAsFavorite: root.markAsFavorite(path, value);
            onOpenProject: root.openProject(path);
            onRemoveProject: root.removeProject(path);
        }
    }

    Rectangle {
        id: rectangle1
        anchors.bottom: mainArea.top
        anchors.bottomMargin: 5
        anchors.rightMargin: 0
        anchors.right: mainArea.right
        anchors.top: parent.top
        anchors.topMargin: 2

        Text {
            text: qsTr("Powered by:")
            anchors.bottom: parent.bottom
            anchors.bottomMargin: 2
            anchors.top: parent.top
            anchors.topMargin: 0
            anchors.rightMargin: 10
            color: "white"
            style: Text.Raised
            styleColor: "black"
            verticalAlignment: Text.AlignVCenter
            anchors.right: logoPy.left
            anchors.leftMargin: 10
        }
        Image {
            id: logoPy
            width: 73
            height: 22
            anchors.rightMargin: 10
            anchors.bottom: parent.bottom
            anchors.bottomMargin: 0
            anchors.top: parent.top
            anchors.topMargin: 0
            antialiasing: true
            fillMode: Image.PreserveAspectFit
            source: "img/powered_py.png"
            anchors.right: logoQt.left
            anchors.leftMargin: 10
        }
        Image {
            id: logoQt
            antialiasing: true
            anchors.top: parent.top
            anchors.topMargin: 0
            anchors.bottom: parent.bottom
            anchors.bottomMargin: 0
            fillMode: Image.PreserveAspectFit
            source: "img/powered_qt.png"
            anchors.right: parent.right
        }
    }

    Text {
        anchors.bottom: parent.bottom
        anchors.left: parent.left
        anchors.leftMargin: parent.height / 14
        anchors.bottomMargin: 5
        color: "black"
        text: qsTr("Copyright © 2011-2013 NINJA-IDE under GPLv3 License agreements")
    }

    function get_padding(item){
        var newPadding = (root._padding - (item.width / 2)) - 10;
        return newPadding;
    }

    function add_project(name, path, favorite){
        projectList.add_project(name, path, favorite);
    }

}

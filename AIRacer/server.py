from Server_Main_Loop.ServerMainLoop import ServerMainLoop
import sys
from PyQt5.QtWidgets import QApplication
from ImageWindow.ImageWindow import RemoteImageWindow

if __name__ == '__main__':
    serverMainLoop = ServerMainLoop()
    serverMainLoop.start()

    app = QApplication(sys.argv)
    imageWindow = RemoteImageWindow(serverMainLoop)
    imageWindow.show()
    imageWindow.start()
    sys.exit(app.exec_())

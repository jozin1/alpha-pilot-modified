import sys
from PyQt5.QtWidgets import QApplication
from settings.settings import Values
from MainLoop.MainLoop import MainLoop

if __name__ == '__main__':

    main_loop = MainLoop()
    main_loop.start()

    if not Values.REMOTE_CONTROL:
        from ImageWindow.ImageWindow import ImageWindow
        app = QApplication(sys.argv)
        imageWindow = ImageWindow(main_loop)
        imageWindow.show()
        imageWindow.start()
        sys.exit(app.exec_())
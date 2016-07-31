#!/usr/bin/env python3

# CLIP -- a program that can recreate a partially-semitransparent image,
# given copies of it with a black background and a white background.
# Copyright (C) 2016  RoadrunnerWMC
# Begun 1/29/14, heavily improved 7/31/16.

# The following license applies only to this single source code file
# (clip.py):

# This file (clip.py) is licensed under the GNU GPL v3.
# algorithm.py is instead licensed under the MIT license.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


VERSION = '1.0'


import os.path
import sys
import time

from PyQt5 import QtCore, QtGui, QtWidgets; Qt = QtCore.Qt

import algorithm



IMAGE_EXTS = ('All Files (*)'
              ';;Bitmap (*.bmp)'
              ';;Joint Photographic Experts Group (*.jpg, *.jpeg)'
              ';;Graphics Interchange Format (*.gif)'
              ';;Portable Network Graphics (*.png)')


class FileInputWidget(QtWidgets.QWidget):
    """
    A widget that provides a convenient way for the user to specify a
    file.
    """

    OPEN = 0
    SAVE = 1

    valueChanged = QtCore.pyqtSignal()

    def __init__(self, exts='', mode=OPEN):
        super().__init__()
        self.exts = exts
        self.mode = mode

        self.filenameTextbox = QtWidgets.QLineEdit()
        self.filenameTextbox.setMinimumWidth(200)
        self.filenameTextbox.textChanged.connect(self.valueChanged.emit)

        self.pickButton = QtWidgets.QPushButton('Choose...')
        self.pickButton.clicked.connect(self.handlePickButtonClicked)

        L = QtWidgets.QHBoxLayout(self)
        L.setContentsMargins(0, 0, 0, 0)
        L.addWidget(self.filenameTextbox)
        L.addWidget(self.pickButton)

    def handlePickButtonClicked(self):
        """
        The user clicked the "Choose" button, so we need to display a
        file-open (or file-save) dialog and update the textbox with
        their selection.
        """
        if self.mode == self.OPEN:
            dlgFunc = QtWidgets.QFileDialog.getOpenFileName
        else:
            dlgFunc = QtWidgets.QFileDialog.getSaveFileName

        fp = dlgFunc(self, 'Choose a filename', '', self.exts)[0]
        if not fp: return

        self.filenameTextbox.setText(fp)

    def value(self):
        """
        Return the current filename, or '' if the current filename is
        nonexistent or invalid.
        """
        fp = self.filenameTextbox.text()
        if self.mode == self.OPEN and not os.path.isfile(fp):
            return ''
        elif self.mode == self.SAVE and (
                os.path.dirname(fp)
                and not os.path.isdir(os.path.dirname(fp))):
            return ''
        return fp


class MainWindow(QtWidgets.QMainWindow):
    """
    The main window for CLIP
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle('CLIP ' + VERSION)
        self.show()

        self.titleLabel = QtWidgets.QLabel(
            'CLIP ' + VERSION + ' by RoadrunnerWMC<br />'
            'Partly licensed under the GNU GPL v3, and partly under the'
            ' MIT license. (See readme.md for details.)<br />'
            '<br />'
            'Choose the input files and output filename below, and then'
            ' hit the "Go!" button to generate the transparent image.')
        self.blackInput = FileInputWidget(IMAGE_EXTS)
        self.whiteInput = FileInputWidget(IMAGE_EXTS)
        self.output = FileInputWidget(IMAGE_EXTS, FileInputWidget.SAVE)
        self.goBtn = QtWidgets.QPushButton('Go!')
        self.goBtn.setEnabled(False)

        self.blackInput.valueChanged.connect(self.handleFilenamesChanged)
        self.whiteInput.valueChanged.connect(self.handleFilenamesChanged)
        self.output.valueChanged.connect(self.handleFilenamesChanged)
        self.goBtn.clicked.connect(self.handleGoBtnClicked)

        centralWidget = QtWidgets.QWidget()
        L = QtWidgets.QFormLayout(centralWidget)
        L.addRow(self.titleLabel)
        L.addRow('Screenshot (black background):', self.blackInput)
        L.addRow('Screenshot (white background):', self.whiteInput)
        L.addRow('Output filename:', self.output)
        L.addRow(self.goBtn)

        self.setCentralWidget(centralWidget)

    def handleFilenamesChanged(self):
        """
        One of the filenames was changed.
        """
        allValid = bool(self.blackInput.value()
                        and self.whiteInput.value()
                        and self.output.value())
        self.goBtn.setEnabled(allValid)

    def handleGoBtnClicked(self):
        """
        The "Go" button was clicked -- run the algorithm
        """

        imgB = QtGui.QImage(self.blackInput.value())
        imgW = QtGui.QImage(self.whiteInput.value())
        outFp = self.output.value()

        if imgB.size() != imgW.size():
            QtWidgets.QMessageBox.warning(self, 'Image Size Error',
                'The given images have different sizes, and therefore cannot'
                ' be used.')
            return

        # Set up an algorithm thread
        self.algorithm = Algorithm_Qt(imgB, imgW)

        # Make a progress dialog and execute it
        ProgDlg = AlgorithmDialog(self.algorithm)
        result = ProgDlg.exec_()

        if not result: # The user canceled it
            self.algorithm.cancel()
            return
        self.algorithm.output.save(outFp)


class AlgorithmDialog(QtWidgets.QDialog):
    """
    A dialog that displays the progress of the algorithm
    """

    def __init__(self, algorithm):
        super().__init__()
        self.setWindowTitle('Progress')

        # Set up the algorithm
        algorithm.rowCompleted.connect(self.handleRowCompleted)
        algorithm.finished.connect(self.handleFinished)
        self.algorithm = algorithm

        # Set up the image preview widget
        self.previewLabel = QtWidgets.QLabel()
        previewScrollArea = QtWidgets.QScrollArea()
        previewScrollArea.setWidget(self.previewLabel)
        previewScrollArea.setMinimumSize(QtCore.QSize(384, 256))
        previewScrollArea.setWidgetResizable(True)
        previewScrollArea.setAlignment(Qt.AlignCenter)
        self.previewLabel.setAlignment(Qt.AlignCenter)

        # Set up the time-remaining label
        t = ''
        t += '<b>Time taken:</b> 0 seconds<br>'
        t += '<b>Estimated time remaining:</b> (calculating)<br>'
        self.timeLabel = QtWidgets.QLabel(t)
        self.timeLabel.setAlignment(Qt.AlignLeft | Qt.AlignBottom)

        # Set up the progress bar
        self.progBar = QtWidgets.QProgressBar()
        self.progBar.setMinimum(0)
        self.progBar.setMaximum(100)
        self.progBar.setValue(0)

        # Set up the button box
        buttonBox = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Cancel)
        buttonBox.rejected.connect(self.reject)

        # Set up the layout
        L = QtWidgets.QGridLayout()
        L.addWidget(previewScrollArea, 0, 0)
        L.addWidget(self.timeLabel, 0, 1)
        L.addWidget(self.progBar, 1, 0, 1, 2)
        L.addWidget(buttonBox, 2, 0, 1, 2)
        L.setRowStretch(0, 1)  # the image should get all of the stretch
        L.setColumnStretch(0, 1)
        self.setLayout(L)

        # Generate the background image
        bgPattern = QtGui.QPixmap(48, 48)
        bgPattern.fill(Qt.white)
        p = QtGui.QPainter(bgPattern)
        p.setBrush(QtGui.QColor('#DDDDDD'))
        p.setPen(Qt.NoPen)
        p.drawRect(0, 0, 24, 24)
        p.drawRect(24, 24, 48, 48)
        del p
        b = QtGui.QBrush()
        b.setTexture(bgPattern)
        self.bgPix = QtGui.QPixmap(algorithm.output.width(),
                            algorithm.output.height())
        self.bgPix.fill(Qt.white)
        p = QtGui.QPainter(self.bgPix)
        p.setBrush(b)
        p.drawRect(-1, -1, self.bgPix.width() + 1, self.bgPix.height() + 1)
        del p

        # Reset stuff
        self.handleRowCompleted(0)
        self.percent = 0.0

        # Refresh the time-remaining every 0.1 seconds
        self.startTime = time.clock()
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.updateTime)
        self.timer.start(100)

    def showEvent(self, e):
        """
        Called when the dialog is about to be shown
        """
        super().showEvent(e)
        self.algorithm.start()

    def handleRowCompleted(self, percent):
        """
        Called when the algorithm completes a row
        """
        if self == None: return # Bug that sometimes happens when the
                                # user closes the dialog
        self.progBar.setValue(percent)
        self.percent = percent

        pix = QtGui.QPixmap(self.bgPix)
        p = QtGui.QPainter(pix)
        p.drawPixmap(0, 0, QtGui.QPixmap.fromImage(self.algorithm.output))
        del p

        self.previewLabel.setPixmap(pix)

    def updateTime(self):
        """
        Updates the time label
        """
        if self.percent <= 0: return
        currentTime = time.clock()
        timeDiff = currentTime - self.startTime
        timeRemaining = (timeDiff * (100 / self.percent)) - timeDiff

        t = ''
        t += '<b>Time taken:</b><br>' + toTimeStr(timeDiff) + '<br><br>'
        t += '<b>Estimated time remaining:</b><br>' + toTimeStr(timeRemaining)
        self.timeLabel.setText(t)

    def handleFinished(self, success):
        """
        Called when the algorithm completes
        """
        if success:
            self.accept()


def toTimeStr(seconds):
    """
    Convert the given number of seconds into a nice string
    """
    secs = int(seconds % 60)
    mins = int(seconds / 60)
    retVal = ''

    if mins == 1:
        retVal = '1 minute, '
    elif mins > 1:
        retVal = '%d minutes, ' % mins
    # If mins == 0, don't bother adding it to the string at all.

    if secs == 1:
        retVal += '1 second'
    else:
        retVal += '%d seconds' % secs

    return retVal


class Algorithm_Qt(QtCore.QObject, algorithm.AbstractAlgorithm):
    """
    An Algorithm class that uses Qt things.
    """

    rowCompleted = QtCore.pyqtSignal(float)
    finished = QtCore.pyqtSignal(bool)

    def __init__(self, blackImage, whiteImage):
        super().__init__()
        self.blackImage = blackImage
        self.whiteImage = whiteImage

        self.width, self.height = blackImage.width(), blackImage.height()
        self.output = QtGui.QImage(
            self.width, self.height,
            QtGui.QImage.Format_ARGB32_Premultiplied)
        self.output.fill(QtGui.QColor.fromRgb(0, 0, 0, 0))

        self.paint = QtGui.QPainter(self.output)

    def getColors(self, x, y):
        blackCol = QtGui.QColor.fromRgba(
            self.blackImage.pixel(x, y))
        whiteCol = QtGui.QColor.fromRgba(
            self.whiteImage.pixel(x, y))
        return ((blackCol.red(), blackCol.green(), blackCol.blue()),
                (whiteCol.red(), whiteCol.green(), whiteCol.blue()))

    def putColor(self, r, g, b, a, x, y):
        self.paint.setPen(QtGui.QPen(QtGui.QColor.fromRgb(r, g, b, a)))
        self.paint.drawPoint(x, y)

    def rowCompletedHandler(self, pct):
        self.rowCompleted.emit(pct)

    def finishedHandler(self, success):
        del self.paint
        self.finished.emit(success)


def main():
    """
    Main startup function
    """
    global app, mainWindow
    app = QtWidgets.QApplication(sys.argv)
    mainWindow = MainWindow()
    sys.exit(app.exec_())

main()

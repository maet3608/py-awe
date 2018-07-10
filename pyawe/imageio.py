import os.path as path
from PyQt4 import QtCore, QtGui
from PyQt4.QtGui import QPainter, QFont, QPen, QBrush, QPolygon, QPixmap
from PyQt4.QtCore import Qt, QPoint, QSize, QRectF, QRect
from aursol.base import AweNode, Group, If
from glob import iglob

import mma.util.imageio as mio


class ImageFileReader(AweNode):
    def __init__(self, filepattern):
        name = 'ImageFileReader:' + filepattern
        AweNode.__init__(self, name)
        self.filepattern = filepattern
        self.reset()

    def process(self):
        try:
            fullpath = path.abspath(next(self.iter))
            image_dataurl = mio.imagefile_to_data_url(fullpath)
            return [fullpath, image_dataurl]
        except StopIteration:
            return None

    def reset(self):
        self.iter = iglob(self.filepattern)


class QtImageAnnotationViewer(QtGui.QWidget):
    def __init__(self, name, size, parent=None):
        super(QtImageAnnotationViewer, self).__init__(parent)
        self.setWindowTitle(name)
        self.name = name
        self.image = None
        self.fullpath = None
        self.resize(*size)

    def show_image(self, fullpath, image_dataurl, polylines):
        image_data, _ = mio.extract_image_and_type(image_dataurl)
        self.fullpath = fullpath
        self.polylines = polylines
        self.image = QtGui.QImage()
        self.image.loadFromData(image_data)
        self.update()

    def _draw_polyline(self, painter, coord):
        polygone = QPolygon([QPoint(x, y) for x, y in coord])
        painter.drawPolygon(polygone)

    def paintEvent(self, event):
        if not self.image: return

        p = QPainter(self)
        ers, sorig = event.rect().size(), self.image.size()
        img_scaled = self.image.scaled(ers, Qt.KeepAspectRatio)
        p.drawImage(QPoint(0, 0), img_scaled)

        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(Qt.green)
        p.drawText(10, 20, self.fullpath)
        p.drawText(10, 40, '#annotations: {}'.format(len(self.polylines)))

        sx = float(img_scaled.size().width()) / sorig.width()
        sy = float(img_scaled.size().height()) / sorig.height()
        p.scale(sx, sy)
        p.setPen(Qt.yellow)
        for polyline in self.polylines:
            self._draw_polyline(p, polyline)


class ImageAnnotationViewer(AweNode):
    def __init__(self, name, size=(600, 600)):
        AweNode.__init__(self, name)
        self.viewer = QtImageAnnotationViewer(name, size)
        self.viewer.show()

    def process(self, fullpath, image_data_url, polylines):
        self.viewer.show_image(fullpath, image_data_url, polylines)
        return [fullpath, image_data_url, polylines]


class QtImageViewer(QtGui.QWidget):
    def __init__(self, name, size, parent=None):
        super(QtImageViewer, self).__init__(parent)
        self.setWindowTitle(name)
        self.name = name
        self.image = None
        self.filename = None
        self.resize(*size)

    def show_image(self, fullpath, image_dataurl):
        image_data, _ = mio.extract_image_and_type(image_dataurl)
        self.filename = fullpath
        self.image = QtGui.QImage()
        self.image.loadFromData(image_data)
        self.update()

    def paintEvent(self, event):
        if not self.image: return
        p = QPainter(self)
        ers, sorig = event.rect().size(), self.image.size()
        img_scaled = self.image.scaled(ers, Qt.KeepAspectRatio)
        p.drawImage(QPoint(0, 0), img_scaled)
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(Qt.green)
        p.drawText(50, 50, self.filename)


class ImageViewer(AweNode):
    def __init__(self, name, size=(600, 600)):
        AweNode.__init__(self, name)
        self.viewer = QtImageViewer(name, size)
        self.viewer.show()

    def process(self, fullpath, image_data_url):
        self.viewer.show_image(fullpath, image_data_url)
        return [fullpath, image_data_url]


class ImageAnnotationWriter(AweNode):
    def __init__(self, name, outdir):
        AweNode.__init__(self, name)
        self.outdir = outdir

    def _draw_polyline(self, painter, coord):
        polygone = QPolygon([QPoint(x, y) for x, y in coord])
        painter.drawPolygon(polygone)

    def process(self, fullpath, image_dataurl, polylines):
        image_data, _ = mio.extract_image_and_type(image_dataurl)
        image = QtGui.QImage()
        image.loadFromData(image_data)
        sis = image.size()
        pixmap = QPixmap(sis.width(), sis.height())
        pixmap.fill(Qt.white)
        p = QPainter()
        p.begin(pixmap)
        p.drawImage(QPoint(0, 0), image)
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(Qt.yellow)
        for polyline in polylines:
            self._draw_polyline(p, polyline)
        p.end()

        _, fname = path.split(fullpath)
        outpath = path.join(self.outdir, fname)
        print(outpath)
        pixmap.save(outpath)

        return [fullpath, image_dataurl, polylines]

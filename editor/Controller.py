import typing

from PyQt5 import QtCore
from PyQt5.QtGui import QColor, QPainter, QPen

from MapData import MapCell, MapData


class Selection:
    Add = 1
    Clear = 2
    
    class Block:
        def __init__(self, data: MapData.Element) -> None:
            self.datax, self.datay = data.x, data.y
            self.data = data
            
        def oddeven(self):
            return (self.datax + self.datay) % 2

    def __init__(self, parent) -> None:
        self.parent = parent
        self.labels: typing.List[Selection.Block] = []
        self.dedup = {}
        
    def paint(self, p: QPainter):
        d: DragController = self.parent.dragger
        dd = d.dragtonorm - d.startnorm
        x, y = dd.x(), dd.y()
        bs = self.parent._blocksize()
        for l in self.labels:
            posx = l.data.x * bs + self.parent.viewOrigin[0]
            posy = l.data.y * bs + self.parent.viewOrigin[1]
            p.fillRect(posx, posy, bs, bs, QColor(255, 255, 0, l.oddeven() and 135 or 90))
            if x or y: # paint select-n-drag blocks if presented
                el: MapData.Element = l.data
                el.src.paint(posx + x, posy + y, bs, bs, p, ghost=True)
        
    def addSelection(self, data: MapData.Element, propertyPanel = True):
        if not data.src:
            return False
        if id(data) in self.dedup:
            return False
        label = Selection.Block(data)
        self.labels.append(label)
        self.dedup[id(data)] = label
        self.parent.selectionEvent(Selection.Add, data)
        if propertyPanel:
            self.parent.findMainWin().propertyPanel.update()
        return True
        
    def delSelection(self, data: MapData.Element):
        if not id(data) in self.dedup:
            return 
        x = self.dedup[id(data)]
        del self.dedup[id(data)]
        self.labels.remove(x)
        self.parent.findMainWin().propertyPanel.update()
        
    def move(self, dx, dy):
        self.parent.data.begin()
        d: MapData = self.parent.data
        for l in self.labels:
            d.delete(l.datax, l.datay)
        for l in self.labels:
            d.put(l.datax + dx, l.datay + dy, l.data)
        self.clear()
            
    def clear(self):
        self.labels = self.labels[:0]
        self.dedup = {}
        self.parent.selectionEvent(Selection.Clear, None)
        self.parent.findMainWin().propertyPanel.update()
        
    def status(self):
        return "{}".format(len(self.labels))

class HoverController:
    def __init__(self, parent) -> None:
        self.parent = parent
        self.labels: typing.List[MapData.Element] = []
        
    def clear(self):
        self.labels = self.labels[:0]
        
    def hold(self, data: typing.List[MapData.Element]):
        self.labels = data
        
    def paint(self, p: QPainter):
        d: DragController = self.parent.dragger
        bs = self.parent._blocksize()
        x, y = d.dragtonorm.x(), d.dragtonorm.y()
        for l in self.labels:
            el: MapData.Element = l
            xx, yy = (l.x - self.labels[0].x) * bs + x, (l.y - self.labels[0].y) * bs + y
            el.src.paint(xx, yy, bs, bs, p, ghost=True)
            for c in el.cascades:
                c.paint(xx, yy, bs, bs, p, ghost=True)
    
    def end(self, cascade):
        if len(self.labels) == 0:
            return
        d: MapData = self.parent.data
        d.begin()

        dd: DragController = self.parent.dragger
        d1, cell, _ = dd.parent.findCellUnder(None, QtCore.QPoint(dd.dragtox, dd.dragtoy))
        cell: MapCell
        
        if cascade and cell and d1 and len(self.labels) == 1:
            old = cell.current.pack()
            cell.current.cascades.append(self.labels[0].src)
            d._appendHistoryPacked(old, cell.current.pack())
        elif d1:
            x, y = self.labels[0].x, self.labels[0].y
            for l in self.labels:
                d.put(l.x - x + d1.x, l.y - y + d1.y, l)

        self.clear()

class DragController:
    Size = 12
    pen = QPen(QColor(100, 120, 120))
    pen.setWidth(3)

    def __init__(self, parent) -> None:
        self.parent = parent
        self.reset()
        
    def reset(self):
        self.startx = 0
        self.starty = 0
        self.dragtox = 0
        self.dragtoy = 0
        self.dragtonorm = self.startnorm = QtCore.QPoint(0, 0)
        self.started = False
        self.visible = True
    
    def start(self, x: int, y: int, normalized: QtCore.QPoint):
        self.startx = self.dragtox = x
        self.starty = self.dragtoy = y
        self.startnorm = self.dragtonorm = normalized
        self.started = True
        
    def drag(self, x: int, y: int, normalized: QtCore.QPoint):
        self.dragtox = x
        self.dragtoy = y
        self.dragtonorm = normalized 
        
    def end(self):
        if not self.started:
            return 0, 0

        d0, _, _ = self.parent.findCellUnder(None, QtCore.QPoint(self.startx, self.starty))
        d1, _, _ = self.parent.findCellUnder(None, QtCore.QPoint(self.dragtox, self.dragtoy))

        self.reset()
        if d0 and d1:
            return d1.x - d0.x, d1.y - d0.y
        return 0, 0
        
    def paint(self, p: QPainter):
        if not self.started:
            return
        if not self.visible:
            return
        DragController._paint(self.startx, self.starty, self.dragtox, self.dragtoy, p)
        
    def _paint(startx, starty, dragtox, dragtoy, p: QPainter):
        p.save()
        p.setPen(DragController.pen)
        p.drawLine(startx, starty, dragtox, dragtoy)

        p.setPen(QPen(QColor(0,0,0,0)))
        p.setBrush(QColor(100, 120, 120, 128))
        offset = 4
        size = DragController.Size + offset
        p.drawEllipse(startx - size / 2, starty - size / 2, size, size)
        p.drawEllipse(dragtox - size / 2, dragtoy - size / 2, size, size)

        p.setBrush(QColor(100, 120, 120))
        p.drawEllipse(startx - DragController.Size / 2, starty - DragController.Size / 2, DragController.Size, DragController.Size)
        p.drawEllipse(dragtox - DragController.Size / 2, dragtoy - DragController.Size / 2, DragController.Size, DragController.Size)
        p.restore()

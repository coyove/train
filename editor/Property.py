import typing
from PyQt5 import QtGui
from PyQt5.QtWidgets import QComboBox, QHBoxLayout, QLabel, QLayout, QMainWindow, QSizePolicy, QSpinBox, QTextEdit, QVBoxLayout, QWidget, qDrawWinButton

from PyQt5 import QtCore
from PyQt5.QtGui import QFontDatabase 

class Property(QWidget):
    def _title(self, t):
        l = QLabel(t, self)
        l.setStyleSheet("font-weight: bold")
        return l 

    def __init__(self, parent: typing.Optional['QWidget']):
        super().__init__(parent=parent)
        # self.box = QVBoxLayout(self)
        # self.box.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
        self.textAttr = QWidget(self)
        self.textAttrBox = QVBoxLayout()
        self.textAttr.setLayout(self.textAttrBox)
        
        self.svgId = QLabel('N/A', self)
        self.historyStatus = QLabel('N/A', self)
        self._addBiBoxInTextAttrBox(self._title('Type'), self.svgId, self._title("Status"), self.historyStatus)

        self.textAttrBox.addWidget(self._title('Text'))
        self.text = QTextEdit(self)
        self.text.textChanged.connect(self.textChanged)
        self.text.installEventFilter(self)
        self.textAttrBox.addWidget(self.text)
        
        self.textFont = QComboBox(self)
        fontFamilies = QFontDatabase()
        for s in fontFamilies.families():
            self.textFont.addItem(s)
        self.textFont.currentIndexChanged.connect(self.fontChanged)
        self.textFont.setEditable(True)
        
        self.textSize = QComboBox(self)
        for i in range(8, 150, 1):
            if i <= 32:
                self.textSize.addItem(str(i))
            elif i <= 80 and i % 2 == 0:
                self.textSize.addItem(str(i))
            elif i % 10 == 0:
                self.textSize.addItem(str(i))
        self.textSize.currentIndexChanged.connect(self.sizeChanged)
        self.textSize.setEditable(True)
        self._addBiBoxInTextAttrBox(self._title("Font Family"), self.textFont, self._title("Font Size"), self.textSize)
        
        self.textAlign = QComboBox(self)
        self.textPlace = QComboBox(self)
        for c in [self.textAlign, self.textPlace]:
            c.addItem('Center', 'c')
            c.addItem('Top', 't')
            c.addItem('Bottom', 'b')
            c.addItem('Left', 'l')
            c.addItem('Right', 'r')
        self.textAlign.currentIndexChanged.connect(self.alignChanged)
        self.textPlace.currentIndexChanged.connect(self.placeChanged)
        self._addBiBoxInTextAttrBox(self._title("Alignment"), self.textAlign, self._title("Placement"), self.textPlace)
        
        self.textX = QSpinBox(self)
        self.textY = QSpinBox(self)
        for c in [self.textX, self.textY]:
            c.setValue(0)
            c.setMinimum(-1e5)
            c.setMaximum(1e5)
        self.textX.valueChanged.connect(lambda e: self.offsetChanged('x', e))
        self.textY.valueChanged.connect(lambda e: self.offsetChanged('y', e))
        self._addBiBoxInTextAttrBox(self._title("Offset X"), self.textX, self._title("Offset Y"), self.textY)

        self.setLayout(self.textAttrBox)
        self.show()
        self.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding)
        
        self.updating = False
        
    def _genVBox(p, w1, w2, m=0):
        placeAttr = QWidget(p)
        placeAttrBox = QVBoxLayout()
        placeAttrBox.setContentsMargins(m, m, m, m)
        placeAttr.setLayout(placeAttrBox)
        placeAttrBox.addWidget(w1)
        placeAttrBox.addWidget(w2)
        return placeAttr
    
    def eventFilter(self, a0, a1: QtCore.QEvent) -> bool:
        if a1.type() == QtCore.QEvent.FocusIn and a0 is self.text:
            self._foreach(lambda x: None)
        return super().eventFilter(a0, a1)

    def _addBiBoxInTextAttrBox(self, t1, w1, t2, w2):
        placeAttr = QWidget(self)
        placeAttrBox = QHBoxLayout()
        placeAttrBox.setContentsMargins(0, 0, 0, 0)
        placeAttr.setLayout(placeAttrBox)
        placeAttrBox.addWidget(Property._genVBox(self, t1, w1))
        placeAttrBox.addWidget(Property._genVBox(self, t2, w2))
        self.textAttrBox.addWidget(placeAttr)
        
    def textChanged(self):
        for x in self.selection():
            x.text = self.text.toPlainText()
        self.findMainWin().mapview.pan(0, 0)
        
    def _foreach(self, f):
        mainData = self.findMainWin().mapview.data
        mainData.begin()
        for x in self.selection():
            old = x.dup()
            f(x)
            mainData._appendHistory(old, x)
        self.findMainWin().mapview.pan(0, 0)
        
    def fontChanged(self, e):
        self._foreach(lambda x: x.set("textFont", self.textFont.itemText(e)))
        
    def offsetChanged(self, t, v):
        self._foreach(lambda x: x.set(t == 'x' and 'textX' or 'textY', v))
        
    def sizeChanged(self, e):
        self._foreach(lambda x: x.set("textSize", int(self.textSize.itemText(e))))
        
    def alignChanged(self, e):
        self._foreach(lambda x: x.set("textAlign", self.textAlign.itemData(e)))
        
    def placeChanged(self, e):
        self._foreach(lambda x: x.set("textPlacement", self.textPlace.itemData(e)))
        
    def findMainWin(self):
        p = self.parent()
        while not isinstance(p, QMainWindow):
            p = p.parent()
        return p
    
    def selection(self):
        if self.updating:
            return []
        return list(map(lambda l: l.data, self.findMainWin().mapview.selector.labels))
    
    def update(self):
        data = self.findMainWin().mapview.data
        self.historyStatus.setText('{}@{}'.format(data.historyCap, len(data.history)))
        for k in self.__dict__:
            w = self.__dict__[k]
            if isinstance(w, QWidget):
                w.setEnabled(False)
        items = self.selection()
        if not items:
            self.svgId.setText("N/A")
            return
        for k in self.__dict__:
            w = self.__dict__[k]
            if isinstance(w, QWidget):
                w.setEnabled(True)
        e = items[-1]
        self.updating = True
        self.svgId.setText(e.data.svgId)
        self.text.setText(e.text)
        self.textFont.setEditText(e.textFont)
        self.textSize.setEditText(str(e.textSize))
        self._setAP(self.textAlign, e.textAlign)
        self._setAP(self.textPlace, e.textPlacement)
        self.updating = False
        
    def _setAP(self, w: QComboBox, d):
        for i in range(0, w.count()):
            if w.itemData(i) == d:
                w.setCurrentIndex(i)
                break

from PyQt5 import QtCore, QtGui, QtWidgets


TABLE_ITEM_SIZE = 76


class HorizontalSelectionTable(QtWidgets.QTableWidget):

    def __init__(self, parent=None):
        super(HorizontalSelectionTable, self).__init__(parent)
        self.setup_ui()
        self.insertRow(0)

    def setup_ui(self):
        self.verticalHeader().hide()
        self.horizontalHeader().hide()
        self.verticalHeader().setDefaultSectionSize(TABLE_ITEM_SIZE - 1)
        self.horizontalHeader().setDefaultSectionSize(TABLE_ITEM_SIZE - 1)

        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectItems)
        self.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)

    def add_item(self, item_data):
        new_item = SelectionTableItem(item_data["name"],
                                      item_data["img"])
        self.insertColumn(self.columnCount())
        self.setCellWidget(0, self.columnCount() - 1,
                           new_item)
        self.resize(self.width() + TABLE_ITEM_SIZE, self.height())
        self.move(self.pos().x() - (TABLE_ITEM_SIZE / 2.0), self.pos().y())

        return new_item


class CategoryPickerTable(HorizontalSelectionTable):

    def __init__(self, mesh_creator, parent=None):
        super(CategoryPickerTable, self).__init__(parent)
        self.category_items = []
        self.category_data = []
        self.mesh_creator = mesh_creator

        self.showing_children = False
        self.mesh_table = None

    def add_item(self, category_data):
        new_item = super(CategoryPickerTable, self)\
            .add_item(category_data)
        self.category_items.append(new_item)
        self.category_data.append(category_data)

        return new_item

    def selectionChanged(self, a=0, b=0):
        selectedIndexes = self.selectedIndexes()
        if len(selectedIndexes) > 0:
            selected_index = selectedIndexes[0].column()

            if not self.showing_children:
                self.show_children(self.category_data[selected_index],
                                   selected_index)
                self.showing_children = True
            else:
                self.mesh_table.setParent(None)
                self.show_children(self.category_data[selected_index],
                                   selected_index)
        else:
            if self.showing_children:
                self.hide_children()
                self.showing_children = True

    def show_children(self, category_data, index):
        self.mesh_table = MeshPickerTable(self.mesh_creator, self.parent())
        # TODO refactor formula
        self.mesh_table.setGeometry(self.pos().x() + self.width() / 2 +
                                    (index - (len(self.category_data) - 1) /
                                    2) * TABLE_ITEM_SIZE,
                                    self.pos().y() - TABLE_ITEM_SIZE, 0,
                                    TABLE_ITEM_SIZE)
        for mesh in category_data["models"]:
            self.mesh_table.add_item(mesh)

        self.mesh_table.raise_()
        self.mesh_table.show()
        self.wrap_child_selection_changed()

    def hide_children(self):
        self.mesh_table.setParent(None)
        self.mesh_table = None

    def wrap_child_selection_changed(self):
        orig_func = self.mesh_table.selectionChanged

        def wrapped(a, b):
            orig_func(a, b)
            self.mesh_table.setParent(None)
            self.mesh_table = None
            self.showing_children = False
            self.clearSelection()
        self.mesh_table.selectionChanged = wrapped


class MeshPickerTable(HorizontalSelectionTable):

    def __init__(self, mesh_creator, parent=None):
        super(MeshPickerTable, self).__init__(parent)
        self.mesh_data = []
        self.mesh_creator = mesh_creator

    def add_item(self, mesh_item):
        if "preview" in mesh_item:
            mesh_item["img"] = mesh_item["preview"]
        new_item = super(MeshPickerTable, self)\
            .add_item(mesh_item)
        self.mesh_data.append(mesh_item)
        return new_item

    def selectionChanged(self, a=0, b=0):
        selectedIndexes = self.selectedIndexes()
        if len(selectedIndexes) > 0:
            selected_index = selectedIndexes[0].column()
            self.mesh_creator.request_add_mesh(
                self.mesh_data[selected_index]["file"],
                self.mesh_data[selected_index]["name"])
        else:
            pass


class SelectionTableItem(QtWidgets.QWidget):

    def __init__(self, name, icon):
        super(SelectionTableItem, self).__init__()
        self.name = name
        self.icon = icon

        self.set_icon(icon)
        self.resize(TABLE_ITEM_SIZE - 1, TABLE_ITEM_SIZE - 1)

    def set_icon(self, icon_src):
        self.icon = icon_src
        icon_label = QtWidgets.QLabel()
        icon_label.resize(TABLE_ITEM_SIZE - 1, TABLE_ITEM_SIZE - 1)
        icon_label.setScaledContents(True)
        icon_label.setPixmap(QtGui.QPixmap(icon_src))

        layout = QtWidgets.QHBoxLayout(self)
        layout.setAlignment(QtCore.Qt.AlignCenter)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.addWidget(icon_label)

        self.setLayout(layout)

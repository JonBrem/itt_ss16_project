from PyQt5 import QtCore, QtGui, QtWidgets


TABLE_ITEM_SIZE = 76


class HorizontalSelectionTable(QtWidgets.QTableWidget):
    """ Main class for the selection bars for the Mesh and
        Texture selection bars in the system.
        Both the "category" bars and the bars for the individual items
        extend this class.

        On a technical level, they are tables (with 1 row), hence
        the name of this class.
    """

    def __init__(self, parent=None):
        super(HorizontalSelectionTable, self).__init__(parent)
        self.setup_ui()
        self.insertRow(0)
        self.setGeometry(0, 0, 0, TABLE_ITEM_SIZE)
        self.create_from_center = True

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
        if self.create_from_center:
            self.move(self.pos().x() - (TABLE_ITEM_SIZE / 2.0), self.pos().y())

        while self.mapToGlobal(QtCore.QPoint(self.pos().x(), 0)).x() < \
                TABLE_ITEM_SIZE:
            self.move(self.pos().x() + 10, self.pos().y())

        return new_item

    def set_create_from_center(self, create_from_center):
        """ If create_from_center is true, the addition of an item
            will cause the table's x position to move to the left by half the
            item's width.
        """
        self.create_from_center = create_from_center


class ExpandableSelectionTable(HorizontalSelectionTable):
    """ The "category selection" bars for the Textures and Meshes
        available in the application.
        When one of its items is clicked, another bar (a ChildSelectionTable)
        pops up, centered over the item that was clicked.
    """

    def __init__(self, item_creator, child_type="Mesh", parent=None):
        super(ExpandableSelectionTable, self).__init__(parent)
        self.category_items = []
        self.category_data = []
        self.item_creator = item_creator

        self.child_type = child_type

        self.showing_children = False
        self.child_table = None

    def add_item(self, category_data):
        new_item = super(ExpandableSelectionTable, self)\
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
                self.child_table.setParent(None)
                self.show_children(self.category_data[selected_index],
                                   selected_index)
        else:
            if self.showing_children:
                self.hide_children()
                self.showing_children = False

    def show_children(self, category_data, index):
        if self.child_type == "Mesh":
            self.child_table = MeshPickerTable(self.item_creator, self.parent())
        else:
            self.child_table = TexturePickerTable(self.item_creator,
                                                  self.parent())

        # center the child table just above the clicked item of this table.
        self.child_table.setGeometry(
            (self.pos().x() + self.width() / 2 +
                (index - (len(self.category_data) - 1) / 2) * TABLE_ITEM_SIZE),
            self.pos().y() - TABLE_ITEM_SIZE, 0, TABLE_ITEM_SIZE)
        for mesh in category_data["models"]:
            self.child_table.add_item(mesh)

        self.child_table.raise_()
        self.child_table.show()
        self.wrap_child_selection_changed()

    def hide_children(self):
        if self.child_table is not None:
            self.child_table.setParent(None)
            self.child_table = None
        self.showing_children = False

    def wrap_child_selection_changed(self):
        orig_func = self.child_table.selectionChanged

        def wrapped(a, b):
            orig_func(a, b)
            if self.child_table is not None:
                self.child_table.setParent(None)
                self.child_table = None
                self.showing_children = False
                self.clearSelection()
        self.child_table.selectionChanged = wrapped

    def lose_focus(self):
        self.clearSelection()
        self.hide_children()


class ChildSelectionTable(HorizontalSelectionTable):
    """ The "item selection" bars that pop up when an item in the
        category selection bars is clicked.
    """

    def __init__(self, parent=None):
        super(ChildSelectionTable, self).__init__(parent)
        self.item_data = []
        self.created_mesh = False

    def add_item(self, item_data):
        if "preview" in item_data:
            item_data["img"] = item_data["preview"]
        new_item = super(ChildSelectionTable, self)\
            .add_item(item_data)
        self.item_data.append(item_data)
        return new_item

    def get_item(self, index):
        return self.item_data[index]


class MeshPickerTable(ChildSelectionTable):
    """ The item selection bar for the meshes.
        A click on an item will add an obect to the scene.
    """

    def __init__(self, mesh_creator, parent=None):
        super(MeshPickerTable, self).__init__(parent)
        self.mesh_creator = mesh_creator
        self.created_mesh = False

    def selectionChanged(self, a=0, b=0):
        selectedIndexes = self.selectedIndexes()
        if len(selectedIndexes) > 0 and not self.created_mesh:
            self.created_mesh = True
            selected_index = selectedIndexes[0].column()
            item = super(MeshPickerTable, self).get_item(selected_index)
            self.mesh_creator.request_add_mesh(
                item["file"], item["name"])
        else:
            pass


class TexturePickerTable(ChildSelectionTable):
    """ The item selection bar for the textures.
        A click on an item will change the wall or floor texture.
    """

    def __init__(self, texture_creator, parent=None):
        super(TexturePickerTable, self).__init__(parent)
        self.texture_creator = texture_creator
        self.created_mesh = False

    def selectionChanged(self, a=0, b=0):
        selectedIndexes = self.selectedIndexes()
        if len(selectedIndexes) > 0 and not self.created_mesh:
            self.created_mesh = True
            selected_index = selectedIndexes[0].column()
            item = super(TexturePickerTable, self).get_item(selected_index)
            self.texture_creator.request_change_texture(
                item["file"], item["name"], item["type"])
        else:
            pass


class SelectionTableItem(QtWidgets.QWidget):
    """ Class for the items in the selection bars.
        The items contain a name and an icon.

        The tables store the corresponding mesh or texture,
        this class is only for the UI of the table item.
    """

    def __init__(self, name, icon):
        super(SelectionTableItem, self).__init__()
        self.name = name
        self.icon = icon

        self.setup_button(name, icon)
        self.resize(TABLE_ITEM_SIZE - 1, TABLE_ITEM_SIZE - 1)

        self.setStyleSheet("""
            * {
                font-size: 8pt;
            }

            *[selectionStyleClass="icon"] {
                padding: 2px 5px 2px 5px;
            }

            *[selectionStyleClass="wrapper"]:hover {
                background-color: #99CCFF;
            }
        """)

        self.setCursor(QtCore.Qt.PointingHandCursor)

    def setup_button(self, name, icon_src):
        icon_label = self.set_icon(icon_src)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setAlignment(QtCore.Qt.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(icon_label)

        name_label = QtWidgets.QLabel()
        name_label.resize(TABLE_ITEM_SIZE - 1, 8)
        name_label.setText(name)
        name_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(name_label)

        # This wrapper is necessary for the hover effect.
        wrapper = QtWidgets.QWidget()
        # any name and value, just so it can be referenced:
        wrapper.setProperty("selectionStyleClass", "wrapper")
        wrapper.setLayout(layout)

        wrapper_layout = QtWidgets.QVBoxLayout(self)
        wrapper_layout.addWidget(wrapper)
        wrapper_layout.setContentsMargins(0, 0, 0, 0)

        self.setLayout(wrapper_layout)

    def set_icon(self, icon_src):
        self.icon = icon_src
        icon_label = QtWidgets.QLabel()
        icon_label.resize(TABLE_ITEM_SIZE - 11, TABLE_ITEM_SIZE - 11)
        icon_label.setScaledContents(True)
        icon_label.setPixmap(QtGui.QPixmap(icon_src))
        # any name and value, just so it can be referenced:
        icon_label.setProperty("selectionStyleClass", "icon")

        return icon_label

import sys
import os
import sqlite3
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QListWidget, QPushButton, QTextEdit,
    QVBoxLayout, QHBoxLayout, QComboBox, QSplitter, QDialog, QLineEdit, QLabel,
    QDialogButtonBox, QListWidgetItem, QAction, QMenu, QColorDialog, QFontDialog,
    QFileDialog
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QTextCharFormat, QTextCursor, QColor, QFont

class RecipeKeeper(QMainWindow):
    def __init__(self, db_path="recipes.db"):
        super().__init__()
        self.db_path = db_path
        self.current_recipe_id = None
        self.sort_option = "Alphabetical"

        # Initialize the database
        self.initialize_db()

        self.setWindowTitle("Recipe Keeper")
        self.resize(900, 600)

        # Apply a dark stylesheet
        self.apply_dark_stylesheet()

        # Create the UI
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)

        self.splitter = QSplitter(Qt.Horizontal)

        # Left panel
        self.init_left_panel()
        self.splitter.addWidget(self.left_panel)

        # Right panel
        self.init_right_panel()
        self.splitter.addWidget(self.right_panel)

        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 2)

        main_layout.addWidget(self.splitter)
        self.setCentralWidget(main_widget)

        # Populate the recipe list
        self.populate_recipe_list()

    def initialize_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS recipes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                ingredients TEXT,
                instructions TEXT,
                tags TEXT DEFAULT NULL,
                color TEXT DEFAULT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()

    def apply_dark_stylesheet(self):
        dark_stylesheet = """
        QMainWindow { background-color: #2A2A2E; }
        QWidget { color: #EEEEEE; background-color: #2A2A2E; font-size: 10pt; }
        QPushButton { background-color: #3C3C40; border: 1px solid #444; padding: 4px 8px; border-radius: 4px; }
        QPushButton:hover { background-color: #4A4A50; }
        QTextEdit { background-color: #333333; color: #EEEEEE; border: 1px solid #444; }
        QListWidget { background-color: #242426; color: #EEEEEE; border: 1px solid #444; }
        QLineEdit, QComboBox { background-color: #3C3C40; color: #EEEEEE; border: 1px solid #444; border-radius: 4px; }
        QMenuBar { background-color: #2A2A2E; }
        """
        self.setStyleSheet(dark_stylesheet)

    def init_left_panel(self):
        self.left_panel = QWidget()
        self.left_layout = QVBoxLayout(self.left_panel)
        self.left_layout.setSpacing(10)

        self.search_line = QLineEdit()
        self.search_line.setPlaceholderText("Type to filter recipes by title or tags...")
        self.search_line.textChanged.connect(self.populate_recipe_list)
        self.left_layout.addWidget(self.search_line)

        self.sort_combobox = QComboBox()
        self.sort_combobox.addItems(["Alphabetical", "Newest First", "Oldest First"])
        self.sort_combobox.currentIndexChanged.connect(self.on_sort_option_change)
        self.left_layout.addWidget(self.sort_combobox)

        self.recipe_list = QListWidget()
        self.recipe_list.itemSelectionChanged.connect(self.display_recipe_content)
        self.left_layout.addWidget(self.recipe_list, 1)

        self.new_recipe_button = QPushButton("New Recipe")
        self.new_recipe_button.clicked.connect(self.open_new_recipe_dialog)
        self.left_layout.addWidget(self.new_recipe_button)

    def init_right_panel(self):
        self.right_panel = QWidget()
        self.right_layout = QVBoxLayout(self.right_panel)
        self.right_layout.setContentsMargins(5, 5, 5, 5)

        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("Enter recipe instructions here...")
        self.text_edit.setContextMenuPolicy(Qt.CustomContextMenu)
        self.text_edit.customContextMenuRequested.connect(self.open_text_context_menu)
        self.right_layout.addWidget(self.text_edit)

        self.ingredients_edit = QTextEdit()
        self.ingredients_edit.setPlaceholderText("Enter ingredients here...")
        self.right_layout.addWidget(self.ingredients_edit)

        self.tags_line_edit = QLineEdit()
        self.tags_line_edit.setPlaceholderText("Add tags separated by commas...")
        self.right_layout.addWidget(self.tags_line_edit)

        self.save_recipe_button = QPushButton("Save Recipe")
        self.save_recipe_button.clicked.connect(self.save_current_recipe)
        self.right_layout.addWidget(self.save_recipe_button)

        self.export_recipes_button = QPushButton("Export Recipes")
        self.export_recipes_button.clicked.connect(self.export_recipes)
        self.right_layout.addWidget(self.export_recipes_button)

    def open_text_context_menu(self, position):
        menu = QMenu()

        bold_action = QAction("Bold", self)
        bold_action.triggered.connect(lambda: self.format_text("bold"))
        menu.addAction(bold_action)

        italic_action = QAction("Italic", self)
        italic_action.triggered.connect(lambda: self.format_text("italic"))
        menu.addAction(italic_action)

        underline_action = QAction("Underline", self)
        underline_action.triggered.connect(lambda: self.format_text("underline"))
        menu.addAction(underline_action)

        menu.addSeparator()

        text_color_action = QAction("Change Text Color", self)
        text_color_action.triggered.connect(self.change_text_color)
        menu.addAction(text_color_action)

        highlight_action = QAction("Change Highlight Color", self)
        highlight_action.triggered.connect(self.change_highlight_color)
        menu.addAction(highlight_action)

        font_size_action = QAction("Change Font Size", self)
        font_size_action.triggered.connect(self.change_font_size)
        menu.addAction(font_size_action)

        menu.exec_(self.text_edit.mapToGlobal(position))

    def format_text(self, format_type):
        cursor = self.text_edit.textCursor()
        if not cursor.hasSelection():
            return

        format = QTextCharFormat()

        if format_type == "bold":
            format.setFontWeight(QFont.Bold)
        elif format_type == "italic":
            format.setFontItalic(True)
        elif format_type == "underline":
            format.setFontUnderline(True)

        cursor.mergeCharFormat(format)

    def change_text_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            cursor = self.text_edit.textCursor()
            format = QTextCharFormat()
            format.setForeground(color)
            cursor.mergeCharFormat(format)

    def change_highlight_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            cursor = self.text_edit.textCursor()
            format = QTextCharFormat()
            format.setBackground(color)
            cursor.mergeCharFormat(format)

    def change_font_size(self):
        cursor = self.text_edit.textCursor()
        if not cursor.hasSelection():
            return

        format = QTextCharFormat()
        font, ok = QFontDialog.getFont()
        if ok:
            format.setFontPointSize(font.pointSize())
            cursor.mergeCharFormat(format)

    def export_recipes(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(self, "Export Recipes", "", "Text Files (*.txt);;HTML Files (*.html);;Markdown Files (*.md)", options=options)
        if file_path:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT title, ingredients, instructions, tags FROM recipes")
            recipes = cursor.fetchall()
            conn.close()

            with open(file_path, "w", encoding="utf-8") as file:
                for title, ingredients, instructions, tags in recipes:
                    file.write(f"Title: {title}\nIngredients: {ingredients}\nTags: {tags}\n\nInstructions:\n{instructions}\n\n{'-'*40}\n\n")

    def on_sort_option_change(self):
        self.sort_option = self.sort_combobox.currentText()
        self.populate_recipe_list()

    def populate_recipe_list(self):
        self.recipe_list.clear()
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        search_text = self.search_line.text()
        query = "SELECT id, title, tags FROM recipes"

        if search_text:
            query += " WHERE title LIKE ? OR tags LIKE ?"
            cursor.execute(query, (f"%{search_text}%", f"%{search_text}%"))
        else:
            if self.sort_option == "Alphabetical":
                query += " ORDER BY title ASC"
            elif self.sort_option == "Newest First":
                query += " ORDER BY created_at DESC"
            elif self.sort_option == "Oldest First":
                query += " ORDER BY created_at ASC"
            cursor.execute(query)

        recipes = cursor.fetchall()
        conn.close()

        for recipe_id, title, tags in recipes:
            item = QListWidgetItem(f"{title} ({tags})")
            item.setData(Qt.UserRole, recipe_id)
            self.recipe_list.addItem(item)

    def display_recipe_content(self):
        selected_item = self.recipe_list.currentItem()
        if not selected_item:
            return

        self.current_recipe_id = selected_item.data(Qt.UserRole)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT ingredients, instructions, tags FROM recipes WHERE id = ?", (self.current_recipe_id,))
        result = cursor.fetchone()
        conn.close()

        if result:
            ingredients, instructions, tags = result
            self.ingredients_edit.setPlainText(ingredients)
            self.text_edit.setHtml(instructions)
            self.tags_line_edit.setText(tags)

    def open_new_recipe_dialog(self):
        dialog = NewRecipeDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            title = dialog.recipe_title.strip()
            if title:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("INSERT INTO recipes (title, ingredients, instructions, tags) VALUES (?, ?, ?, ?)", (title, "", "", ""))
                conn.commit()
                conn.close()
                self.populate_recipe_list()

    def save_current_recipe(self):
        if not self.current_recipe_id:
            print("No recipe selected to save!")
            return

        ingredients = self.ingredients_edit.toPlainText()
        instructions = self.text_edit.toHtml()
        tags = self.tags_line_edit.text()
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("UPDATE recipes SET ingredients = ?, instructions = ?, tags = ? WHERE id = ?", (ingredients, instructions, tags, self.current_recipe_id))
        conn.commit()
        conn.close()
        self.populate_recipe_list()

class NewRecipeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.recipe_title = ""
        self.setWindowTitle("Create New Recipe")
        self.setFixedSize(300, 100)

        layout = QVBoxLayout()
        self.setLayout(layout)

        label = QLabel("Enter recipe title:")
        layout.addWidget(label)

        self.line_edit = QLineEdit()
        layout.addWidget(self.line_edit)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept_data)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def accept_data(self):
        self.recipe_title = self.line_edit.text()
        self.accept()

def main():
    app = QApplication(sys.argv)
    app.setFont(QFont("Arial"))
    window = RecipeKeeper()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()

import tkinter as tk
from tkinter import messagebox
import sqlite3

try:
    import difflib
except Exception:
    difflib = None

try:
    import folium
except Exception:
    folium = None

import webbrowser
import os
import tempfile


class Mosque:
    def __init__(self, ID, name, type_, address, coordinates, Imam_name):
        self.ID = ID
        self.name = name
        self.type = type_
        self.address = address
        self.coordinates = coordinates
        self.Imam_name = Imam_name

    def as_tuple(self):
        return (self.ID, self.name, self.type, self.address, self.coordinates, self.Imam_name)

    def __str__(self):
        return f"ID={self.ID} | Name={self.name} | Type={self.type} | Address={self.address} | Coordinates={self.coordinates} | Imam={self.Imam_name}"


class Database:
    def __init__(self):
        self.conn = sqlite3.connect("mosques.db")
        self.cur = self.conn.cursor()
        self.cur.execute(
            """
            CREATE TABLE IF NOT EXISTS Mosq (
                ID INTEGER PRIMARY KEY,
                name TEXT,
                type TEXT,
                address TEXT,
                coordinates TEXT,
                Imam_name TEXT
            )
            """
        )
        self.conn.commit()

    def Display(self):
        self.cur.execute("SELECT ID, name, type, address, coordinates, Imam_name FROM Mosq ORDER BY ID")
        return self.cur.fetchall()

    def Search(self, name):
        self.cur.execute(
            "SELECT ID, name, type, address, coordinates, Imam_name FROM Mosq WHERE name = ? LIMIT 1",
            (name,)
        )
        return self.cur.fetchone()

    def Insert(self, ID, name, type, address, coordinates, Imam_name):
        self.cur.execute(
            "INSERT INTO Mosq (ID, name, type, address, coordinates, Imam_name) VALUES (?, ?, ?, ?, ?, ?)",
            (ID, name, type, address, coordinates, Imam_name)
        )
        self.conn.commit()

    def Delete(self, ID):
        self.cur.execute("DELETE FROM Mosq WHERE ID = ?", (ID,))
        self.conn.commit()

    def UpdateImamByID(self, ID, Imam_name):
        self.cur.execute("UPDATE Mosq SET Imam_name = ? WHERE ID = ?", (Imam_name, ID))
        self.conn.commit()

    def GetAllNames(self):
        self.cur.execute("SELECT name FROM Mosq")
        return [row[0] for row in self.cur.fetchall()]

    def __del__(self):
        try:
            self.conn.close()
        except Exception:
            pass


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Mosques Management System")

        self.db = Database()
        self.last_searched_id = None
        self.last_searched_name = None

        self.id_var = tk.StringVar()
        self.name_var = tk.StringVar()
        self.type_var = tk.StringVar(value="Masjid")
        self.address_var = tk.StringVar()
        self.coord_var = tk.StringVar()
        self.imam_var = tk.StringVar()

        self.build_ui()

    def build_ui(self):
        main = tk.Frame(self.root, padx=10, pady=10)
        main.pack(fill="both", expand=True)

        left = tk.Frame(main)
        left.grid(row=0, column=0, sticky="n")

        right = tk.Frame(main)
        right.grid(row=0, column=1, padx=(15, 0), sticky="nsew")

        main.grid_columnconfigure(1, weight=1)
        main.grid_rowconfigure(0, weight=1)

        tk.Label(left, text="ID").grid(row=0, column=0, sticky="w")
        tk.Entry(left, textvariable=self.id_var, width=25).grid(row=0, column=1, pady=3)

        tk.Label(left, text="Name").grid(row=1, column=0, sticky="w")
        tk.Entry(left, textvariable=self.name_var, width=25).grid(row=1, column=1, pady=3)

        tk.Label(left, text="Type").grid(row=2, column=0, sticky="w")
        types = ["Masjid", "Jame", "Other"]
        tk.OptionMenu(left, self.type_var, *types).grid(row=2, column=1, sticky="ew", pady=3)

        tk.Label(left, text="Address").grid(row=3, column=0, sticky="w")
        tk.Entry(left, textvariable=self.address_var, width=25).grid(row=3, column=1, pady=3)

        tk.Label(left, text="Coordinates").grid(row=4, column=0, sticky="w")
        tk.Entry(left, textvariable=self.coord_var, width=25).grid(row=4, column=1, pady=3)

        tk.Label(left, text="Imam_name").grid(row=5, column=0, sticky="w")
        tk.Entry(left, textvariable=self.imam_var, width=25).grid(row=5, column=1, pady=3)

        btns = tk.Frame(left, pady=10)
        btns.grid(row=6, column=0, columnspan=2, sticky="ew")

        tk.Button(btns, text="Display All", width=14, command=self.display_all).grid(row=0, column=0, padx=3, pady=3)
        tk.Button(btns, text="Search By Name", width=14, command=self.search_by_name).grid(row=0, column=1, padx=3, pady=3)
        tk.Button(btns, text="Update Entry", width=14, command=self.update_entry).grid(row=0, column=2, padx=3, pady=3)

        tk.Button(btns, text="Add Entry", width=14, command=self.add_entry).grid(row=1, column=0, padx=3, pady=3)
        tk.Button(btns, text="Delete Entry", width=14, command=self.delete_entry).grid(row=1, column=1, padx=3, pady=3)
        tk.Button(btns, text="Display on Map", width=14, command=self.display_on_map).grid(row=1, column=2, padx=3, pady=3)

        tk.Label(right, text="Records").pack(anchor="w")
        list_frame = tk.Frame(right)
        list_frame.pack(fill="both", expand=True)

        self.listbox = tk.Listbox(list_frame, width=80, height=18)
        self.listbox.pack(side="left", fill="both", expand=True)

        scroll = tk.Scrollbar(list_frame, command=self.listbox.yview)
        scroll.pack(side="right", fill="y")
        self.listbox.config(yscrollcommand=scroll.set)

        self.listbox.bind("<<ListboxSelect>>", self.on_select)

    def clear_listbox(self):
        self.listbox.delete(0, tk.END)

    def fill_listbox(self, rows):
        self.clear_listbox()
        for row in rows:
            m = Mosque(*row)
            self.listbox.insert(tk.END, str(m))

    def on_select(self, event):
        if not self.listbox.curselection():
            return
        text = self.listbox.get(self.listbox.curselection()[0])
        try:
            part = text.split("|")[0].strip()
            ID = int(part.replace("ID=", "").strip())
            row = self.get_row_by_id(ID)
            if row:
                self.set_fields_from_row(row)
        except Exception:
            pass

    def get_row_by_id(self, ID):
        rows = self.db.Display()
        for r in rows:
            if r[0] == ID:
                return r
        return None

    def set_fields_from_row(self, row):
        self.id_var.set(row[0])
        self.name_var.set(row[1])
        self.type_var.set(row[2])
        self.address_var.set(row[3])
        self.coord_var.set(row[4])
        self.imam_var.set(row[5])

    def display_all(self):
        rows = self.db.Display()
        self.fill_listbox(rows)

    def search_by_name(self):
        name = self.name_var.get().strip()
        if not name:
            messagebox.showinfo("Info", "Enter a mosque name to search.")
            return

        row = self.db.Search(name)
        if row:
            self.fill_listbox([row])
            self.last_searched_id = row[0]
            self.last_searched_name = row[1]
        else:
            self.last_searched_id = None
            self.last_searched_name = None
            self.clear_listbox()
            self.listbox.insert(tk.END, "No exact match found.")
            if difflib is not None:
                names = self.db.GetAllNames()
                close = difflib.get_close_matches(name, names, n=5, cutoff=0.6)
                if close:
                    self.listbox.insert(tk.END, "Close matches:")
                    for n in close:
                        self.listbox.insert(tk.END, n)

    def add_entry(self):
        ID_txt = self.id_var.get().strip()
        name = self.name_var.get().strip()
        type_ = self.type_var.get().strip()
        address = self.address_var.get().strip()
        coords = self.coord_var.get().strip()
        imam = self.imam_var.get().strip()

        if not ID_txt or not name:
            messagebox.showinfo("Info", "ID and Name are required.")
            return

        try:
            ID = int(ID_txt)
        except ValueError:
            messagebox.showinfo("Info", "ID must be a number.")
            return

        mosque = Mosque(ID, name, type_, address, coords, imam)

        try:
            self.db.Insert(*mosque.as_tuple())
            messagebox.showinfo("Info", "Entry added.")
            self.display_all()
        except sqlite3.IntegrityError:
            messagebox.showinfo("Info", "This ID already exists.")
        except Exception as e:
            messagebox.showinfo("Info", f"Error: {e}")

    def delete_entry(self):
        ID_txt = self.id_var.get().strip()
        if not ID_txt:
            messagebox.showinfo("Info", "Enter ID to delete.")
            return
        try:
            ID = int(ID_txt)
        except ValueError:
            messagebox.showinfo("Info", "ID must be a number.")
            return

        self.db.Delete(ID)
        messagebox.showinfo("Info", "Entry deleted (if existed).")
        self.display_all()

    def update_entry(self):
        if self.last_searched_id is None:
            messagebox.showinfo("Info", "Search by Name first, then update Imam_name.")
            return
        imam = self.imam_var.get().strip()
        if not imam:
            messagebox.showinfo("Info", "Enter Imam_name to update.")
            return

        self.db.UpdateImamByID(self.last_searched_id, imam)
        messagebox.showinfo("Info", "Imam_name updated.")
        self.display_all()

    def display_on_map(self):
        coords = self.coord_var.get().strip()
        name = self.name_var.get().strip() or "Mosque"

        if not coords:
            messagebox.showinfo("Info", "Enter Coordinates like: 26.3, 43.8")
            return

        if folium is None:
            messagebox.showinfo("Info", "folium is not installed on this machine.")
            return

        try:
            parts = coords.replace(" ", "").split(",")
            lat = float(parts[0])
            lon = float(parts[1])
        except Exception:
            messagebox.showinfo("Info", "Coordinates format should be: lat,lon")
            return

        m = folium.Map(location=[lat, lon], zoom_start=14)
        folium.Marker([lat, lon], popup=name).add_to(m)

        fd, path = tempfile.mkstemp(suffix=".html")
        os.close(fd)
        m.save(path)
        webbrowser.open("file://" + os.path.abspath(path))


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()

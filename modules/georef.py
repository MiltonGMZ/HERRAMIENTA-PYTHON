import pandas as pd
from thefuzz import process
import customtkinter as ctk
from tkinter import filedialog, messagebox, Toplevel
import threading
import os
import re
from infrastructure.normalizer import TextNormalizer

class GeorefModule(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)

        self.title("GeoJudicial Masivo Pro v4.1 - Milton Murillo")
        self.geometry("850x750")
        self.after(10, self.lift) # Traer al frente
        
        self.df_maestro = None
        self.esta_procesando = False
        self.cache_busquedas = {}
        
        self.setup_ui()

    def setup_ui(self):
        self.main_frame = ctk.CTkFrame(self, corner_radius=20, border_width=2, border_color="#566573")
        self.main_frame.pack(pady=20, padx=20, fill="both", expand=True)

        self.header_label = ctk.CTkLabel(
            self.main_frame, 
            text="⚙️ GEO-REFERENCIADOR JUDICIAL PRO", 
            font=("Segoe UI", 24, "bold"),
            text_color="#5DADE2"
        )
        self.header_label.pack(pady=(25, 10))
        
        self.btn_container = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.btn_container.pack(pady=20, padx=40, fill="x")

        self.btn_maestro = ctk.CTkButton(
            self.btn_container, 
            text="📂 1. CARGAR MAPA JUDICIAL", 
            command=self.cargar_maestro, 
            height=50, 
            font=("Arial", 14, "bold"),
            fg_color="#2E4053"
        )
        self.btn_maestro.pack(pady=10, fill="x")

        self.btn_procesar = ctk.CTkButton(
            self.btn_container, 
            text="⚡ 2. INICIAR PROCESO MASIVO", 
            command=self.solicitar_archivo_y_columna, 
            height=50, 
            font=("Arial", 14, "bold"),
            fg_color="#D35400"
        )
        self.btn_procesar.pack(pady=10, fill="x")

        self.progress_bar = ctk.CTkProgressBar(self.main_frame, width=600, height=15, progress_color="#27AE60")
        self.progress_bar.pack(pady=20, padx=40)
        self.progress_bar.set(0)

        self.status_box = ctk.CTkTextbox(self.main_frame, height=200, font=("Consolas", 12))
        self.status_box.pack(pady=(10, 20), padx=40, fill="both", expand=True)

    def log(self, mensaje):
        self.status_box.insert("end", f" [LOG] > {mensaje}\n")
        self.status_box.see("end")

    def cargar_maestro(self):
        ruta = filedialog.askopenfilename(filetypes=[("Excel/CSV", "*.xlsx *.csv")])
        if ruta:
            try:
                self.df_maestro = pd.read_excel(ruta) if ruta.endswith('.xlsx') else pd.read_csv(ruta)
                self.df_maestro.columns = self.df_maestro.columns.str.strip()
                # Usamos el normalizador central
                self.df_maestro['NOMBRE_NORM'] = self.df_maestro['NOMBRE DESPACHO'].apply(TextNormalizer.normalize)
                self.btn_maestro.configure(text=f"✅ BASE LISTA: {len(self.df_maestro)} REGISTROS", fg_color="#1D8348")
                self.log("Mapa Judicial cargado correctamente.")
            except Exception as e:
                messagebox.showerror("Error", f"Falla al cargar: {e}")

    def solicitar_archivo_y_columna(self):
        if self.df_maestro is None:
            messagebox.showwarning("Falta Base", "Primero debes cargar el Mapa Judicial.")
            return
        ruta_masiva = filedialog.askopenfilename()
        if not ruta_masiva: return
        df_temp = pd.read_excel(ruta_masiva, nrows=0) if not ruta_masiva.endswith('.csv') else pd.read_csv(ruta_masiva, nrows=0)
        self.abrir_ventana_seleccion(ruta_masiva, df_temp.columns.tolist())

    def abrir_ventana_seleccion(self, ruta, columnas):
        ventana = Toplevel(self)
        ventana.title("Configurar Columna")
        ventana.geometry("400x300")
        ventana.configure(bg="#1B2631")
        ventana.grab_set()

        ctk.CTkLabel(ventana, text="Seleccione la columna con los juzgados:").pack(pady=20)
        combo = ctk.CTkComboBox(ventana, values=columnas, width=250)
        combo.pack(pady=10)

        def confirmar():
            col = combo.get()
            ventana.destroy()
            threading.Thread(target=self.procesar_datos, args=(ruta, col), daemon=True).start()

        ctk.CTkButton(ventana, text="🚀 EMPEZAR", command=confirmar, fg_color="#27AE60").pack(pady=20)

    def procesar_datos(self, ruta, col_busqueda):
        try:
            self.btn_procesar.configure(state="disabled", text="⏳ PROCESANDO...")
            df_lista = pd.read_excel(ruta) if not ruta.endswith('.csv') else pd.read_csv(ruta)
            
            nombres_ref = self.df_maestro['NOMBRE_NORM'].tolist()
            mapa_datos = self.df_maestro.set_index('NOMBRE_NORM').to_dict('index')
            
            total = len(df_lista)
            resultados = []
            for i, nombre_original in enumerate(df_lista[col_busqueda]):
                nombre_limpio = TextNormalizer.normalize(nombre_original)
                if nombre_limpio in ["", "NAN", "NONE"]:
                    res = {'JUZGADO_REF': 'NO TIENE JUZGADO', 'CONFIANZA': '0%'}
                elif nombre_limpio in self.cache_busquedas:
                    res = self.cache_busquedas[nombre_limpio]
                else:
                    match, score = process.extractOne(nombre_limpio, nombres_ref)
                    if score > 65:
                        info = mapa_datos[match]
                        res = {'JUZGADO_REF': match, 'MUNICIPIO': info.get('MUNICIPIO', 'N/D'), 'CONFIANZA': f"{score}%"}
                    else:
                        res = {'JUZGADO_REF': 'NO TIENE JUZGADO', 'CONFIANZA': f"{score}%"}
                    self.cache_busquedas[nombre_limpio] = res
                
                resultados.append({**df_lista.iloc[i].to_dict(), **res})
                self.progress_bar.set((i + 1) / total)

            df_final = pd.DataFrame(resultados)
            ruta_save = filedialog.asksaveasfilename(defaultextension=".xlsx")
            if ruta_save:
                df_final.to_excel(ruta_save, index=False)
                messagebox.showinfo("¡Hecho!", "Proceso finalizado.")
        except Exception as e:
            self.log(f"ERROR: {e}")
        finally:
            self.btn_procesar.configure(state="normal", text="⚡ 2. INICIAR PROCESO MASIVO")
            self.progress_bar.set(0)
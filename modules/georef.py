import pandas as pd
from thefuzz import process
import customtkinter as ctk
from tkinter import filedialog, messagebox, Toplevel
import threading
import os
import re

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
        
        ctk.CTkLabel(self.main_frame, text="Módulo Integrado | Milton Murillo", font=("Arial", 11, "italic")).pack()

        self.btn_container = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.btn_container.pack(pady=20, padx=40, fill="x")

        self.btn_maestro = ctk.CTkButton(
            self.btn_container, 
            text="📂 1. CARGAR MAPA JUDICIAL", 
            command=self.cargar_maestro, 
            height=50, 
            font=("Arial", 14, "bold"),
            fg_color="#2E4053",
            hover_color="#1B2631",
            border_width=1,
            border_color="#ABB2B9"
        )
        self.btn_maestro.pack(pady=10, fill="x")

        self.btn_procesar = ctk.CTkButton(
            self.btn_container, 
            text="⚡ 2. INICIAR PROCESO MASIVO", 
            command=self.solicitar_archivo_y_columna, 
            height=50, 
            font=("Arial", 14, "bold"),
            fg_color="#D35400", 
            hover_color="#A04000"
        )
        self.btn_procesar.pack(pady=10, fill="x")

        self.progress_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.progress_frame.pack(pady=10, padx=40, fill="x")
        
        self.label_progreso = ctk.CTkLabel(self.progress_frame, text="Esperando archivos...", font=("Arial", 12))
        self.label_progreso.pack()

        self.progress_bar = ctk.CTkProgressBar(self.progress_frame, height=15, progress_color="#27AE60")
        self.progress_bar.pack(pady=5, fill="x")
        self.progress_bar.set(0)

        self.status_box = ctk.CTkTextbox(
            self.main_frame, 
            height=200, 
            font=("Consolas", 12), 
            fg_color="#1C2833", 
            text_color="#D5D8DC",
            border_width=1,
            border_color="#566573"
        )
        self.status_box.pack(pady=(10, 20), padx=40, fill="both", expand=True)

        self.btn_reset = ctk.CTkButton(
            self.main_frame, 
            text="🔄 Limpiar Módulo", 
            command=self.reset_sistema, 
            width=120, 
            height=30, 
            fg_color="#7B241C", 
            font=("Arial", 11)
        )
        self.btn_reset.pack(pady=(0, 20))

    def log(self, mensaje):
        self.status_box.insert("end", f" [LOG] > {mensaje}\n")
        self.status_box.see("end")

    def reset_sistema(self):
        self.df_maestro = None
        self.cache_busquedas = {}
        self.btn_maestro.configure(text="📂 1. CARGAR MAPA JUDICIAL", fg_color="#2E4053")
        self.progress_bar.set(0)
        self.label_progreso.configure(text="Esperando archivos...")
        self.status_box.delete("1.0", "end")
        self.log("Módulo reseteado.")

    def limpiar_texto(self, texto):
        if pd.isna(texto): return ""
        t = str(texto).upper().strip()
        t = re.sub(r'[^A-Z0-9 ]', '', t)
        return t

    def cargar_maestro(self):
        ruta = filedialog.askopenfilename(filetypes=[("Excel/CSV", "*.xlsx *.xlsm *.csv")])
        if ruta:
            try:
                self.log(f"Cargando base: {os.path.basename(ruta)}")
                if ruta.endswith('.csv'):
                    self.df_maestro = pd.read_csv(ruta)
                else:
                    self.df_maestro = pd.read_excel(ruta, engine='openpyxl')
                
                self.df_maestro.columns = self.df_maestro.columns.str.strip()
                # Ajustamos para que busque la columna correcta en tu mapa judicial
                if 'NOMBRE DESPACHO' in self.df_maestro.columns:
                    self.df_maestro = self.df_maestro.drop_duplicates(subset=['NOMBRE DESPACHO'])
                    self.df_maestro['NOMBRE_NORM'] = self.df_maestro['NOMBRE DESPACHO'].apply(self.limpiar_texto)
                    self.btn_maestro.configure(text=f"✅ BASE LISTA: {len(self.df_maestro)} REGISTROS", fg_color="#1D8348")
                    self.log("Mapa Judicial cargado correctamente.")
                else:
                    messagebox.showerror("Error", "La base no tiene la columna 'NOMBRE DESPACHO'")
            except Exception as e:
                messagebox.showerror("Error", f"Falla al cargar: {e}")

    def solicitar_archivo_y_columna(self):
        if self.df_maestro is None:
            messagebox.showwarning("Falta Base", "Primero debes cargar el Mapa Judicial.")
            return
        
        ruta_masiva = filedialog.askopenfilename(filetypes=[("Excel/CSV", "*.xlsx *.xlsm *.csv")])
        if not ruta_masiva: return

        try:
            temp_df = pd.read_csv(ruta_masiva, nrows=0) if ruta_masiva.endswith('.csv') else pd.read_excel(ruta_masiva, engine='openpyxl', nrows=0)
            self.abrir_ventana_seleccion(ruta_masiva, temp_df.columns.tolist())
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def abrir_ventana_seleccion(self, ruta, columnas):
        ventana = Toplevel(self)
        ventana.title("Configuración de Búsqueda")
        ventana.geometry("450x350")
        ventana.configure(bg="#1B2631")
        ventana.transient(self)
        ventana.grab_set()

        ctk.CTkLabel(ventana, text="SELECCIONE COLUMNA ORIGEN", font=("Arial", 16, "bold"), text_color="#F39C12").pack(pady=20)
        
        combo = ctk.CTkComboBox(ventana, values=columnas, width=300)
        combo.pack(pady=15)
        combo.set(columnas[0])

        def confirmar():
            col = combo.get()
            ventana.destroy()
            self.esta_procesando = True
            threading.Thread(target=self.procesar_datos, args=(ruta, col), daemon=True).start()

        ctk.CTkButton(ventana, text="🚀 EMPEZAR PROCESO", command=confirmar, fg_color="#27AE60").pack(pady=30)

    def procesar_datos(self, ruta, col_busqueda):
        try:
            self.btn_procesar.configure(state="disabled", text="⏳ PROCESANDO...")
            df_lista = pd.read_csv(ruta) if ruta.endswith('.csv') else pd.read_excel(ruta, engine='openpyxl')
            
            nombres_ref = self.df_maestro['NOMBRE_NORM'].tolist()
            mapa_datos = self.df_maestro.set_index('NOMBRE_NORM').to_dict('index')
            
            total = len(df_lista)
            resultados = []
            encontrados = 0

            for i, nombre_original in enumerate(df_lista[col_busqueda]):
                progreso = (i + 1) / total
                self.progress_bar.set(progreso)
                self.label_progreso.configure(text=f"Analizando: {i+1} de {total} ({int(progreso*100)}%)")
                
                nombre_limpio = self.limpiar_texto(nombre_original)
                
                if nombre_limpio in ["", "NAN", "NONE", "NULL"]:
                    res = {'JUZGADO_REF': 'VACÍO', 'MUNICIPIO': 'N/D', 'DISTRITO': 'N/D', 'CONFIANZA': '0%'}
                elif nombre_limpio in self.cache_busquedas:
                    res = self.cache_busquedas[nombre_limpio]
                    if res['JUZGADO_REF'] != 'VACÍO': encontrados += 1
                else:
                    match, score = process.extractOne(nombre_limpio, nombres_ref)
                    if score > 65:
                        info = mapa_datos[match]
                        res = {
                            'JUZGADO_REF': match,
                            'MUNICIPIO': info.get('MUNICIPIO', 'N/D'),
                            'DISTRITO': info.get('DISTRITO', 'N/D'),
                            'CODIGO_DTO': info.get('CODIGO DESPACHO', '0'),
                            'CONFIANZA': f"{score}%"
                        }
                        encontrados += 1
                    else:
                        res = {'JUZGADO_REF': 'BAJA COINCIDENCIA', 'MUNICIPIO': 'N/D', 'CONFIANZA': f"{score}%"}
                    self.cache_busquedas[nombre_limpio] = res
                
                resultados.append({**df_lista.iloc[i].to_dict(), **res})

            df_final = pd.DataFrame(resultados)
            
            ruta_save = filedialog.asksaveasfilename(defaultextension=".xlsx", initialfile="Georef_Suite_Pro.xlsx")
            if ruta_save:
                df_final.to_excel(ruta_save, index=False)
                messagebox.showinfo("Suite Judicial", f"Proceso Exitoso\nAciertos: {encontrados}/{total}")
            
        except Exception as e:
            self.log(f"ERROR: {e}")
        finally:
            self.btn_procesar.configure(state="normal", text="⚡ 2. INICIAR PROCESO MASIVO")
            self.progress_bar.set(0)
            self.esta_procesando = False
import pandas as pd
import customtkinter as ctk
from tkinter import filedialog, messagebox, Toplevel
import threading
import os
from difflib import SequenceMatcher, get_close_matches
from infrastructure.normalizer import TextNormalizer

class ReconciliadorModule(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Reconciliador Pro - Milton Murillo")
        self.geometry("900x800")
        self.after(10, self.lift)
        
        self.data_a = {"ruta": None, "hoja": None, "header_row": 0}
        self.data_b = {"ruta": None, "hoja": None, "header_row": 0}
        
        self.sel_cols_a = {"col_busca": ""}
        self.widgets_a = {}
        self.widgets_b = {}
        
        self.setup_ui()

    def setup_ui(self):
        self.main_scroll = ctk.CTkScrollableFrame(self)
        self.main_scroll.pack(pady=20, padx=20, fill="both", expand=True)

        ctk.CTkLabel(self.main_scroll, text="⚖️ RECONCILIACIÓN DE DESPACHOS",
                    font=("Arial", 22, "bold"), text_color="#E67E22").pack(pady=15)

        self.create_card(self.main_scroll, "1. ARCHIVO A VALIDAR (LISTADO REPETIDO)", "A")
        self.frame_a = ctk.CTkFrame(self.main_scroll, fg_color="#1B2631", corner_radius=10)
        self.frame_a.pack(fill="x", padx=40, pady=5)

        self.create_card(self.main_scroll, "2. BASE DE REFERENCIA (DESPLEGADOS)", "B")
        self.frame_b = ctk.CTkFrame(self.main_scroll, fg_color="#1B2631", corner_radius=10)
        self.frame_b.pack(fill="x", padx=40, pady=5)

        self.metrics_frame = ctk.CTkFrame(self.main_scroll, border_width=1, border_color="#566573")
        self.metrics_frame.pack(pady=20, padx=40, fill="x")
        
        self.lbl_stats = ctk.CTkLabel(self.metrics_frame, text="Esperando configuración de archivos...", font=("Arial", 13, "italic"))
        self.lbl_stats.pack(pady=10)

        self.progress_bar = ctk.CTkProgressBar(self.metrics_frame, orientation="horizontal", height=15)
        self.progress_bar.pack(pady=10, padx=20, fill="x")
        self.progress_bar.set(0)

        self.btn_run = ctk.CTkButton(self.main_scroll, text="⚡ EJECUTAR RECONCILIACIÓN", 
                                     fg_color="#27AE60", height=55, font=("Arial", 15, "bold"), 
                                     command=self.iniciar_proceso)
        self.btn_run.pack(pady=10, padx=40, fill="x")

        self.txt_log = ctk.CTkTextbox(self.main_scroll, height=200, font=("Consolas", 11), fg_color="#1C2833")
        self.txt_log.pack(pady=10, padx=40, fill="x")

    def log(self, msj):
        self.txt_log.insert("end", f"> {msj}\n")
        self.txt_log.see("end")

    def create_card(self, parent, title, tipo):
        f = ctk.CTkFrame(parent, fg_color="#2E4053")
        f.pack(pady=10, padx=40, fill="x")
        ctk.CTkLabel(f, text=title, font=("Arial", 12, "bold")).pack(pady=5)
        ctk.CTkButton(f, text="Cargar Excel", command=lambda: self.cargar(tipo)).pack(pady=10)

    def cargar(self, tipo):
        ruta = filedialog.askopenfilename(filetypes=[("Excel", "*.xlsx *.xlsm")])
        if not ruta: return
        try:
            hojas = pd.ExcelFile(ruta).sheet_names
            self.abrir_selector(ruta, hojas, tipo)
        except Exception as e:
            messagebox.showerror("Error", f"Falla lectura: {e}")

    def abrir_selector(self, ruta, hojas, tipo):
        v = Toplevel(self)
        v.title(f"Configurar Libro {tipo}")
        v.geometry("400x250")
        v.grab_set()

        ctk.CTkLabel(v, text=f"Seleccione Hoja ({tipo}):", font=("Arial", 13)).pack(pady=20)
        sel_hoja = ctk.CTkComboBox(v, values=hojas, width=250)
        sel_hoja.pack()
        sel_hoja.set(hojas[0])

        def confirmar():
            hoja_sel = sel_hoja.get()
            idx_h = 0 if tipo == "A" else self.detectar_encabezado(ruta, hoja_sel)
            df_temp = pd.read_excel(ruta, sheet_name=hoja_sel, header=idx_h, nrows=2)
            cols = [str(c).strip() for c in df_temp.columns]
            
            if tipo == "A":
                self.data_a.update({"ruta": ruta, "hoja": hoja_sel, "header_row": idx_h})
                self.render_config_a(cols)
            else:
                self.data_b.update({"ruta": ruta, "hoja": hoja_sel, "header_row": idx_h})
                self.render_config_b(cols)
                self.state('zoomed') # Maximiza al cargar el archivo B
            
            v.destroy()
            self.log(f"Libro {tipo} configurado.")

        ctk.CTkButton(v, text="Confirmar", command=confirmar).pack(pady=30)

    def detectar_encabezado(self, ruta, hoja):
        df_scan = pd.read_excel(ruta, sheet_name=hoja, header=None, nrows=15)
        mejor_fila = 0
        max_texto = -1
        for i, row in df_scan.iterrows():
            score = sum(1 for x in row if isinstance(x, str) and len(str(x).strip()) > 2)
            if score > max_texto:
                max_texto = score
                mejor_fila = i
        return mejor_fila

    def render_config_a(self, cols):
        for child in self.frame_a.winfo_children(): child.destroy()
        row = ctk.CTkFrame(self.frame_a, fg_color="transparent")
        row.pack(pady=10, padx=10, fill="x")
        ctk.CTkLabel(row, text="Columna Despacho:").pack(side="left", padx=10)
        cb = ctk.CTkComboBox(row, values=cols, width=350)
        cb.pack(side="left")
        self.widgets_a["col_busca"] = cb

    def render_config_b(self, cols):
        for child in self.frame_b.winfo_children(): child.destroy()
        lbls = {"col_nombre": "📌 Nombre Despacho:", "col_estado": "🚥 Columna Estado:"}
        for k, txt in lbls.items():
            r = ctk.CTkFrame(self.frame_b, fg_color="transparent")
            r.pack(fill="x", pady=2)
            ctk.CTkLabel(r, text=txt, width=150).pack(side="left")
            cb = ctk.CTkComboBox(r, values=cols, width=350)
            cb.pack(side="left", padx=5)
            self.widgets_b[k] = cb

    def calcular_similitud(self, a, b):
        return SequenceMatcher(None, a, b).ratio()

    def iniciar_proceso(self):
        try:
            self.sel_cols_a["col_busca"] = self.widgets_a["col_busca"].get()
            self.btn_run.configure(state="disabled", text="PROCESANDO...")
            self.progress_bar.configure(mode="indeterminate")
            self.progress_bar.start()
            threading.Thread(target=self.ejecutar, daemon=True).start()
        except Exception as e:
            self.log(f"Error: {e}")

    def ejecutar(self):
        try:
            self.log("🚀 Iniciando Reconciliación Cruzada...")
            df_a = pd.read_excel(self.data_a["ruta"], sheet_name=self.data_a["hoja"], header=self.data_a["header_row"])
            df_b = pd.read_excel(self.data_b["ruta"], sheet_name=self.data_b["hoja"], header=self.data_b["header_row"])

            c_a = self.sel_cols_a["col_busca"]
            c_b_nom = self.widgets_b["col_nombre"].get()
            c_b_est = self.widgets_b["col_estado"].get()
            
            # 1. Agrupación Archivo 1
            df_resumen = df_a.groupby(c_a).size().reset_index(name='CANTIDAD_USUARIOS')
            total_unicos_a = len(df_resumen)

            # 2. Preparar Referencia
            # Usamos fillna para que si el estado está vacío, no rompa la lógica
            df_b[c_b_est] = df_b[c_b_est].fillna("DESPLEGADO") # Asumimos desplegado si hay match y está vacío
            df_b['NORM_REF'] = df_b[c_b_nom].astype(str).apply(TextNormalizer.normalize)
            
            dict_ref = {
                row['NORM_REF']: (row[c_b_nom], str(row[c_b_est])) 
                for _, row in df_b.iterrows()
            }
            lista_norm_b = list(dict_ref.keys())

            estados_finales, matches, similitudes = [], [], []

            for _, fila in df_resumen.iterrows():
                n_orig = str(fila[c_a])
                n_norm = TextNormalizer.normalize(n_orig)
                
                encontrado = None
                score = 0.0

                if n_norm in dict_ref:
                    encontrado = n_norm
                    score = 1.0
                else:
                    cercanos = get_close_matches(n_norm, lista_norm_b, n=1, cutoff=0.93)
                    if cercanos:
                        encontrado = cercanos[0]
                        score = self.calcular_similitud(n_norm, encontrado)

                if encontrado:
                    nombre_ref, estado_ref = dict_ref[encontrado]
                    est_limpio = estado_ref.strip().lower()
                    
                    # LÓGICA FLEXIBLE: Si está vacío, dice "nan" o dice "desplegado" -> ES DESPLEGADO
                    if est_limpio in ["desplegado", "nan", "none", ""]:
                        estados_finales.append("DESPLEGADO")
                    else:
                        estados_finales.append(f"SIN DESPLEGAR ({estado_ref.upper()})")
                    
                    matches.append(nombre_ref)
                    similitudes.append(score)
                else:
                    estados_finales.append("NO ENCONTRADO EN REF")
                    matches.append("N/A")
                    similitudes.append(0.0)

            df_resumen['ESTADO_VALIDADO'] = estados_finales
            df_resumen['SIMILITUD'] = [f"{s*100:.1f}%" for s in similitudes]
            df_resumen['NOMBRE_EN_REFERENCIA'] = matches

            # 3. Conteos Finales
            si_desplegados = sum(1 for e in estados_finales if e == "DESPLEGADO")
            no_desplegados = total_unicos_a - si_desplegados

            self.log("✅ ANÁLISIS COMPLETADO")
            
            path = filedialog.asksaveasfilename(defaultextension=".xlsx", initialfile="Resultado_Reconciliacion.xlsx")
            if path:
                df_resumen.to_excel(path, index=False)
                
                resumen_msj = (
                    f"ESTADÍSTICAS FINALES:\n\n"
                    f"• Despachos en Archivo 1: {total_unicos_a}\n"
                    f"• Desplegados confirmados: {si_desplegados}\n"
                    f"• Pendientes o No encontrados: {no_desplegados}\n\n"
                    f"Se incluyeron coincidencias con estado vacío como Desplegados."
                )
                messagebox.showinfo("Suite Judicial - Milton Murillo", resumen_msj)

        except Exception as e:
            self.log(f"Error Crítico: {e}")
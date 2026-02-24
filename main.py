import customtkinter as ctk
from modules.georef import GeorefModule
from modules.reconciliador import ReconciliadorModule

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class DashboardMilton(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Suite Judicial Pro - Milton Murillo")
        self.geometry("600x550")
        self.resizable(False, False)

        self.frame = ctk.CTkFrame(self, corner_radius=20, border_width=2)
        self.frame.pack(pady=30, padx=30, fill="both", expand=True)

        self.label = ctk.CTkLabel(
            self.frame, 
            text="🏢 SUITE JUDICIAL PRO", 
            font=("Segoe UI", 26, "bold"),
            text_color="#5DADE2"
        )
        self.label.pack(pady=(30, 10))

        ctk.CTkLabel(self.frame, text="Módulos de Automatización", font=("Arial", 12)).pack()

        # Botón 1: Georreferenciador
        self.btn_geo = ctk.CTkButton(
            self.frame,
            text="📍 GEORREFERENCIADOR MASIVO\n(Búsqueda Difusa + Mapa Judicial)",
            height=90, font=("Arial", 14, "bold"),
            fg_color="#2E4053", hover_color="#1B2631",
            command=self.abrir_georef
        )
        self.btn_geo.pack(pady=20, padx=50, fill="x")

        # Botón 2: Reconciliador
        self.btn_recon = ctk.CTkButton(
            self.frame,
            text="⚖️ RECONCILIADOR DE DESPACHOS\n(Validación de Despliegue - Clean Arch)",
            height=90, font=("Arial", 14, "bold"),
            fg_color="#D35400", hover_color="#A04000",
            command=self.abrir_reconciliador
        )
        self.btn_recon.pack(pady=20, padx=50, fill="x")

        self.footer = ctk.CTkLabel(self.frame, text="v4.5 Platinum Edition - Milton Murillo", font=("Arial", 10))
        self.footer.pack(side="bottom", pady=20)

    def abrir_georef(self):
        GeorefModule(self)

    def abrir_reconciliador(self):
        ReconciliadorModule(self)

if __name__ == "__main__":
    app = DashboardMilton()
    app.mainloop()
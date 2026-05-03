import argostranslate.package
import argostranslate.translate

print("Actualizando índice de paquetes...")
argostranslate.package.update_package_index()

print("Buscando modelo inglés → español...")
available = argostranslate.package.get_available_packages()
pkg = next(p for p in available if p.from_code == "en" and p.to_code == "es")

print("Descargando e instalando modelo...")
argostranslate.package.install_from_path(pkg.download())

print("✅ Modelo instalado correctamente.")
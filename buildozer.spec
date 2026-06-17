[app]

# (str) Título de la app (lo que verá el usuario)
title = Laberinto

# (str) Nombre del paquete (sin espacios, minúsculas)
package.name = laberinto

# (str) Dominio del paquete (puede ser cualquier cosa, estilo "org.tunombre")
package.domain = org.tunombre

# (str) Carpeta donde está main.py
source.dir = .

# (list) Extensiones de archivo a incluir (este juego no usa imágenes/sonidos externos)
source.include_exts = py

# (str) Versión de la app
version = 1.0

# (list) Requisitos. "pygame" hace que python-for-android use
# automáticamente el bootstrap "pygame" (no se necesita Kivy).
requirements = python3,pygame==2.5.2

# (str) Orientación: landscape, portrait o all
orientation = portrait

# (bool) Pantalla completa
fullscreen = 1

# (list) Permisos de Android que necesita la app (este juego no necesita ninguno)
android.permissions =

# (int) API de Android objetivo para compilar
android.api = 34

# (int) API mínima de Android soportada (21 = Android 5.0)
android.minapi = 24

# (str) Versión del NDK a usar
android.ndk = 23b

# (list) Arquitecturas a compilar (cubre prácticamente todos los celulares actuales)
android.archs = arm64-v8a, armeabi-v7a

# (bool) Acepta automáticamente las licencias del SDK.
# IMPRESCINDIBLE para que funcione en GitHub Actions (sin esto el build se cuelga).
android.accept_sdk_license = True

# (bool) Permite backup de datos de la app
android.allow_backup = True

# (str) Pantalla de carga e ícono (opcional, descomenta y pon tu archivo si quieres)
# icon.filename = %(source.dir)s/icon.png
# presplash.filename = %(source.dir)s/presplash.png


[buildozer]

# (int) Nivel de log: 0 = solo errores, 1 = info, 2 = debug (recomendado para detectar fallos)
log_level = 2

# (int) Mostrar advertencia si se corre como root
warn_on_root = 1

import pygame as pg
import random
import sys
import os

# ==================== DETECCIÓN DE PLATAFORMA ====================
ANDROID = False
try:
    import android
    ANDROID = True
except ImportError:
    pass

# ==================== INICIALIZACIÓN ====================
pg.init()

if ANDROID:
    # Pantalla completa en Android
    info = pg.display.Info()
    SW, SH = info.current_w, info.current_h
    SCREEN = pg.display.set_mode((SW, SH), pg.FULLSCREEN)
else:
    SW, SH = 1000, 800
    SCREEN = pg.display.set_mode((SW, SH))

pg.display.set_caption("Laberinto")

# ===================== CONFIGURACIÓN ====================
BORDE = 10
# Celda más pequeña en pantallas chicas para que quepa el laberinto
CELDA = max(40, min(60, SH // 14))
GROSOR = 3

# Zona del laberinto (parte superior, deja espacio abajo para botones)
BTN_AREA_H = int(SH * 0.28)   # 28% inferior para botones táctiles
MAZE_H = SH - BTN_AREA_H

AX = BORDE
AY = BORDE
AW = SW - BORDE * 2
AH = MAZE_H - BORDE * 2

COLS  = AW // CELDA
FILAS = AH // CELDA

# =================== GENERACIÓN DEL AVATAR ==============
TARGET_SIZE = CELDA - GROSOR * 4

def crear_avatar():
    SIZE = TARGET_SIZE
    dirs_labels = ["DER", "IZQ", "ARR", "ABA"]
    eye_offsets = {
        "DER": (SIZE // 5, 0),
        "IZQ": (-SIZE // 5, 0),
        "ARR": (0, -SIZE // 5),
        "ABA": (0, SIZE // 5),
    }
    result = {}
    for label in dirs_labels:
        frames = []
        for i in range(4):
            surf = pg.Surface((SIZE, SIZE), pg.SRCALPHA)
            # Cuerpo
            pg.draw.circle(surf, (50, 130, 220), (SIZE//2, SIZE//2), SIZE//2)
            pg.draw.circle(surf, (100, 190, 255), (SIZE//2, SIZE//2), SIZE//2, 2)
            # Ojo animado
            ox, oy = eye_offsets[label]
            bounce = [0, 2, 0, -2][i]
            eye_r = max(3, SIZE // 10)
            pg.draw.circle(surf, (255, 255, 255),
                           (SIZE//2 + ox, SIZE//2 + oy + bounce), eye_r)
            pg.draw.circle(surf, (0, 0, 0),
                           (SIZE//2 + ox + (1 if ox > 0 else -1 if ox < 0 else 0),
                            SIZE//2 + oy + bounce), max(1, eye_r // 2))
            frames.append(surf)
        result[label] = frames
    return result["DER"], result["IZQ"], result["ARR"], result["ABA"]

AD, AI, AR, AB = crear_avatar()

# ==================== GENERADOR DE LABERINTO ====================
def generar_laberinto(cols, filas):
    paredes  = [[{'D': True, 'B': True} for _ in range(cols)] for _ in range(filas)]
    visitado = [[False] * cols for _ in range(filas)]

    def vecinos(f, c):
        v = []
        if f > 0:         v.append((f-1, c, 'A'))
        if f < filas - 1: v.append((f+1, c, 'B'))
        if c > 0:         v.append((f, c-1, 'I'))
        if c < cols - 1:  v.append((f, c+1, 'D'))
        return v

    pila = [(0, 0)]
    visitado[0][0] = True
    while pila:
        f, c = pila[-1]
        no_vis = [(nf, nc, d) for nf, nc, d in vecinos(f, c) if not visitado[nf][nc]]
        if no_vis:
            nf, nc, d = random.choice(no_vis)
            if d == 'D': paredes[f][c]['D']  = False
            if d == 'B': paredes[f][c]['B']  = False
            if d == 'I': paredes[nf][nc]['D'] = False
            if d == 'A': paredes[nf][nc]['B'] = False
            visitado[nf][nc] = True
            pila.append((nf, nc))
        else:
            pila.pop()
    return paredes

def construir_rects_paredes(paredes):
    rects = []
    rects.append(pg.Rect(AX, AY, AW, GROSOR))
    rects.append(pg.Rect(AX, AY + AH - GROSOR, AW, GROSOR))
    rects.append(pg.Rect(AX, AY, GROSOR, AH))
    rects.append(pg.Rect(AX + AW - GROSOR, AY, GROSOR, AH))
    for f in range(FILAS):
        for c in range(COLS):
            x = AX + c * CELDA
            y = AY + f * CELDA
            if paredes[f][c]['D'] and c < COLS - 1:
                rects.append(pg.Rect(x + CELDA - GROSOR, y, GROSOR * 2, CELDA + GROSOR))
            if paredes[f][c]['B'] and f < FILAS - 1:
                rects.append(pg.Rect(x, y + CELDA - GROSOR, CELDA + GROSOR, GROSOR * 2))
    return rects

# ==================== POWER-UPS ====================
class PowerUp(pg.sprite.Sprite):
    TIPOS = {
        "velocidad": {"color": (255, 200, 0),   "icono": "V", "duracion": 5000},
        "vision":    {"color": (100, 255, 200),  "icono": "?", "duracion": 7000},
    }
    def __init__(self, celda_col, celda_fil, tipo):
        super().__init__()
        self.tipo = tipo
        cfg = self.TIPOS[tipo]
        self.image = pg.Surface((TARGET_SIZE, TARGET_SIZE), pg.SRCALPHA)
        pg.draw.circle(self.image, cfg["color"],
                       (TARGET_SIZE//2, TARGET_SIZE//2), TARGET_SIZE//2)
        font = pg.font.Font(None, max(16, TARGET_SIZE // 2))
        txt = font.render(cfg["icono"], True, (0, 0, 0))
        self.image.blit(txt, (TARGET_SIZE//2 - txt.get_width()//2,
                              TARGET_SIZE//2 - txt.get_height()//2))
        cx = AX + celda_col * CELDA + CELDA // 2
        cy = AY + celda_fil * CELDA + CELDA // 2
        self.rect   = self.image.get_rect(center=(cx, cy))
        self.hitbox = pg.Rect(0, 0, TARGET_SIZE, TARGET_SIZE)
        self.hitbox.center = (cx, cy)
        self.duracion = cfg["duracion"]

def crear_powerups(paredes, n=6):
    powerups = pg.sprite.Group()
    usadas   = {(0, 0), (FILAS-1, COLS-1)}
    tipos    = list(PowerUp.TIPOS.keys())
    intentos = 0
    while len(powerups) < n and intentos < 200:
        intentos += 1
        f = random.randint(1, FILAS - 2)
        c = random.randint(1, COLS - 2)
        if (f, c) not in usadas:
            usadas.add((f, c))
            powerups.add(PowerUp(c, f, random.choice(tipos)))
    return powerups

# ==================== JUGADOR ====================
class Jugador(pg.sprite.Sprite):
    def __init__(self, pos, rects_paredes):
        super().__init__()
        self.ani_derecha   = AD
        self.ani_izquierda = AI
        self.ani_arriba    = AR
        self.ani_abajo     = AB

        self.index     = 0.0
        self.speed     = max(3, CELDA // 15)
        self.speed_base = self.speed
        self.direction = "ABJ_F"
        self.image     = self.ani_abajo[0]

        self.hitbox = pg.Rect(0, 0, TARGET_SIZE, TARGET_SIZE)
        self.hitbox.center = pos
        self.rect   = self.image.get_rect()
        self.rect.center = self.hitbox.center

        self.rects_paredes  = rects_paredes
        self.powerup_activo = None
        self.powerup_fin_ms = 0
        self.vision_activa  = False

    def _actualizar_imagen(self):
        if self.index >= 4:
            self.index = 0.0
        d = self.direction
        if   d == "DER": self.image = self.ani_derecha[int(self.index)];   self.index += 0.2
        elif d == "IZQ": self.image = self.ani_izquierda[int(self.index)]; self.index += 0.2
        elif d == "ARR": self.image = self.ani_arriba[int(self.index)];    self.index += 0.2
        elif d == "ABJ": self.image = self.ani_abajo[int(self.index)];     self.index += 0.2
        else:
            if   "DER" in d: self.image = self.ani_derecha[0]
            elif "IZQ" in d: self.image = self.ani_izquierda[0]
            elif "ARR" in d: self.image = self.ani_arriba[0]
            elif "ABJ" in d: self.image = self.ani_abajo[0]

    def _mover(self, dx, dy):
        self.hitbox.x += dx
        for rect in self.rects_paredes:
            if self.hitbox.colliderect(rect):
                if dx > 0: self.hitbox.right = rect.left
                else:      self.hitbox.left  = rect.right
        self.hitbox.y += dy
        for rect in self.rects_paredes:
            if self.hitbox.colliderect(rect):
                if dy > 0: self.hitbox.bottom = rect.top
                else:      self.hitbox.top    = rect.bottom

    def procesar_entrada(self, keys, touch_dx=0, touch_dy=0):
        dx, dy = 0, 0
        # Teclado (PC)
        if keys[pg.K_a] or keys[pg.K_LEFT]:  dx = -self.speed; self.direction = "IZQ"
        elif keys[pg.K_d] or keys[pg.K_RIGHT]: dx = self.speed; self.direction = "DER"
        if keys[pg.K_w] or keys[pg.K_UP]:   dy = -self.speed; self.direction = "ARR"
        elif keys[pg.K_s] or keys[pg.K_DOWN]: dy = self.speed; self.direction = "ABJ"

        # Táctil (Android)
        if touch_dx != 0: dx = touch_dx * self.speed; self.direction = "DER" if touch_dx > 0 else "IZQ"
        if touch_dy != 0: dy = touch_dy * self.speed; self.direction = "ABJ" if touch_dy > 0 else "ARR"

        if dx == 0 and dy == 0:
            if "_" not in self.direction:
                self.direction += "_F"
        else:
            self._mover(dx, dy)

    def aplicar_powerup(self, tipo, ahora_ms):
        self.powerup_activo = tipo
        self.powerup_fin_ms = ahora_ms + PowerUp.TIPOS[tipo]["duracion"]
        if tipo == "velocidad": self.speed = self.speed_base + 4
        elif tipo == "vision":  self.vision_activa = True

    def actualizar_powerups(self, ahora_ms):
        if self.powerup_activo and ahora_ms >= self.powerup_fin_ms:
            if self.powerup_activo == "velocidad": self.speed = self.speed_base
            elif self.powerup_activo == "vision":  self.vision_activa = False
            self.powerup_activo = None

    def update(self):
        self._actualizar_imagen()
        self.rect = self.image.get_rect()
        self.rect.center = self.hitbox.center

# ==================== BOTONES TÁCTILES ====================
class Boton:
    """Botón circular para control táctil en Android."""
    def __init__(self, cx, cy, radio, etiqueta, color=(60, 60, 80)):
        self.cx     = cx
        self.cy     = cy
        self.radio  = radio
        self.label  = etiqueta
        self.color  = color
        self.activo = False   # True mientras el dedo lo presiona
        self.rect   = pg.Rect(cx - radio, cy - radio, radio*2, radio*2)

    def dibujar(self, surf):
        alpha_surf = pg.Surface((self.radio*2, self.radio*2), pg.SRCALPHA)
        color_uso  = (min(self.color[0]+60, 255),
                      min(self.color[1]+60, 255),
                      min(self.color[2]+60, 255), 200) if self.activo else (*self.color, 160)
        pg.draw.circle(alpha_surf, color_uso, (self.radio, self.radio), self.radio)
        pg.draw.circle(alpha_surf, (200, 200, 220, 220), (self.radio, self.radio), self.radio, 3)
        surf.blit(alpha_surf, (self.cx - self.radio, self.cy - self.radio))
        font = pg.font.Font(None, self.radio)
        txt  = font.render(self.label, True, (255, 255, 255))
        surf.blit(txt, (self.cx - txt.get_width()//2, self.cy - txt.get_height()//2))

    def contiene(self, px, py):
        return (px - self.cx)**2 + (py - self.cy)**2 <= self.radio**2


def crear_botones():
    """Crea el D-pad táctil en la zona inferior de la pantalla."""
    zona_y  = MAZE_H + BTN_AREA_H // 2   # centro vertical de la zona de botones
    radio   = int(BTN_AREA_H * 0.30)
    paso    = int(radio * 2.3)
    cx_base = SW // 4                    # lado izquierdo para el D-pad

    arr  = Boton(cx_base,        zona_y - radio - 4, radio, "▲")
    aba  = Boton(cx_base,        zona_y + radio + 4, radio, "▼")
    izq  = Boton(cx_base - paso, zona_y,             radio, "◄")
    der  = Boton(cx_base + paso, zona_y,             radio, "►")
    return {"ARR": arr, "ABJ": aba, "IZQ": izq, "DER": der}

# ==================== NIEBLA DE GUERRA ====================
def dibujar_niebla(jugador, radio=140):
    fog = pg.Surface((SW, SH), pg.SRCALPHA)
    fog.fill((0, 0, 0, 210))
    cx, cy = jugador.rect.center
    for r in range(radio, 0, -4):
        alpha = max(0, int(210 * (1 - r / radio)))
        pg.draw.circle(fog, (0, 0, 0, alpha), (cx, cy), r)
    SCREEN.blit(fog, (0, 0))

# ==================== DIBUJO ====================
def dibujar_laberinto(rects_paredes, nivel):
    colores = [(30,30,30),(20,40,80),(60,20,20),(20,60,20)]
    color   = colores[(nivel - 1) % len(colores)]
    for rect in rects_paredes:
        pg.draw.rect(SCREEN, color, rect)

def dibujar_inicio_fin(inicio_rect, fin_rect):
    for rect, color, borde, txt_str in [
        (inicio_rect, (50,200,50),  (100,255,100), "START"),
        (fin_rect,    (200,50,50),  (255,100,100), "META"),
    ]:
        pg.draw.rect(SCREEN, color, rect)
        pg.draw.rect(SCREEN, borde, rect, 3)
        font = pg.font.Font(None, max(14, CELDA // 4))
        txt  = font.render(txt_str, True, (255,255,255))
        SCREEN.blit(txt, (rect.centerx - txt.get_width()//2,
                          rect.centery - txt.get_height()//2))

def dibujar_zona_botones(botones):
    """Fondo semitransparente de la zona de controles táctiles."""
    zona = pg.Surface((SW, BTN_AREA_H), pg.SRCALPHA)
    zona.fill((20, 20, 30, 180))
    SCREEN.blit(zona, (0, MAZE_H))
    for btn in botones.values():
        btn.dibujar(SCREEN)

def dibujar_hud(nivel, tiempo, jugador, ahora_ms):
    font = pg.font.Font(None, max(18, SW // 40))
    SCREEN.blit(font.render(f"Nivel: {nivel}",   True, (20,20,20)), (20, 8))
    SCREEN.blit(font.render(f"Tiempo: {tiempo}s", True, (20,20,20)), (20, 28))
    if jugador.powerup_activo:
        restante = max(0, (jugador.powerup_fin_ms - ahora_ms) // 1000)
        cfg = PowerUp.TIPOS[jugador.powerup_activo]
        txt = font.render(f"[{jugador.powerup_activo.upper()}] {restante}s", True, cfg["color"])
        SCREEN.blit(txt, (SW - txt.get_width() - 15, 8))

def dibujar_victoria(nivel, tiempo):
    overlay = pg.Surface((SW, SH), pg.SRCALPHA)
    overlay.fill((0, 0, 0, 200))
    SCREEN.blit(overlay, (0, 0))
    f1 = pg.font.Font(None, max(60, SW // 10))
    f2 = pg.font.Font(None, max(32, SW // 18))
    f3 = pg.font.Font(None, max(22, SW // 26))
    t1 = f1.render("¡GANASTE!", True, (80, 220, 80))
    t2 = f2.render(f"Tiempo: {tiempo}s", True, (255, 255, 255))
    t3 = f3.render("Toca la pantalla → Nivel siguiente", True, (180, 180, 180))
    for t, oy in [(t1, -100), (t2, -20), (t3, 50)]:
        SCREEN.blit(t, (SW//2 - t.get_width()//2, SH//2 + oy))

# ==================== LOOP PRINCIPAL ====================
def main():
    FPS   = 60
    CLOCK = pg.time.Clock()

    nivel        = 1
    ganado       = False
    tiempo_ganado = 0
    tiempo_inicio = pg.time.get_ticks()

    INICIO_X    = AX + CELDA // 2
    INICIO_Y    = AY + CELDA // 2
    INICIO_RECT = pg.Rect(AX + GROSOR, AY + GROSOR,
                          CELDA - GROSOR*2, CELDA - GROSOR*2)
    FIN_RECT    = pg.Rect(AX + (COLS-1)*CELDA + GROSOR,
                          AY + (FILAS-1)*CELDA + GROSOR,
                          CELDA - GROSOR*2, CELDA - GROSOR*2)

    def nuevo_nivel():
        paredes = generar_laberinto(COLS, FILAS)
        rects   = construir_rects_paredes(paredes)
        pups    = crear_powerups(paredes, n=6)
        return paredes, rects, pups

    paredes, rects_paredes, powerups = nuevo_nivel()
    jugador = Jugador((INICIO_X, INICIO_Y), rects_paredes)
    sprites = pg.sprite.Group(jugador)
    botones = crear_botones()

    fondos = [(240,240,235),(220,230,245),(245,220,220),(220,245,220)]

    # Estado del D-pad táctil
    touch_ids   = {}   # finger_id → nombre_boton
    touch_dx    = 0
    touch_dy    = 0

    cerrar = False
    while not cerrar:
        CLOCK.tick(FPS)
        ahora_ms     = pg.time.get_ticks()
        tiempo_actual = (ahora_ms - tiempo_inicio) // 1000

        for event in pg.event.get():
            if event.type == pg.QUIT:
                cerrar = True

            # ---- Teclado (PC) ----
            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    cerrar = True
                elif event.key == pg.K_SPACE and ganado:
                    ganado = False

            # ---- Toque en pantalla (Android) ----
            elif event.type == pg.FINGERDOWN:
                px = int(event.x * SW)
                py = int(event.y * SH)
                for nombre, btn in botones.items():
                    if btn.contiene(px, py):
                        btn.activo = True
                        touch_ids[event.finger_id] = nombre
                # Toque fuera de botones en pantalla de victoria → siguiente nivel
                if ganado:
                    ganado = False

            elif event.type == pg.FINGERUP:
                nombre = touch_ids.pop(event.finger_id, None)
                if nombre and nombre in botones:
                    botones[nombre].activo = False

            # ---- Clic ratón PC (para probar sin Android) ----
            elif event.type == pg.MOUSEBUTTONDOWN and ganado:
                ganado = False

        # Calcular dirección táctil activa
        touch_dx = touch_dy = 0
        for nombre, btn in botones.items():
            if btn.activo:
                if nombre == "DER": touch_dx =  1
                elif nombre == "IZQ": touch_dx = -1
                elif nombre == "ABJ": touch_dy =  1
                elif nombre == "ARR": touch_dy = -1

        # Siguiente nivel
        if not ganado and nivel > 0 and \
           all(not btn.activo for btn in botones.values()) and \
           tiempo_ganado > 0 and False:   # placeholder, se controla arriba
            pass

        # Reiniciar tras victoria
        if not ganado and tiempo_ganado > 0 and \
           not any(b.activo for b in botones.values()):
            # Se detecta el cambio de ganado arriba con FINGERDOWN/MOUSEBUTTONDOWN
            pass

        # Reset de nivel cuando ganado pasa a False
        # (usamos una variable auxiliar para detectar el cambio)
        SCREEN.fill(fondos[(nivel - 1) % len(fondos)])
        dibujar_laberinto(rects_paredes, nivel)
        dibujar_inicio_fin(INICIO_RECT, FIN_RECT)
        powerups.draw(SCREEN)

        if not ganado:
            jugador.actualizar_powerups(ahora_ms)
            keys = pg.key.get_pressed()
            jugador.procesar_entrada(keys, touch_dx, touch_dy)
            sprites.update()

            for pu in list(powerups.sprites()):
                if jugador.hitbox.colliderect(pu.hitbox):
                    jugador.aplicar_powerup(pu.tipo, ahora_ms)
                    pu.kill()

            sprites.draw(SCREEN)

            if not jugador.vision_activa:
                dibujar_niebla(jugador)

            dibujar_zona_botones(botones)
            dibujar_hud(nivel, tiempo_actual, jugador, ahora_ms)

            if jugador.hitbox.colliderect(FIN_RECT):
                ganado       = True
                tiempo_ganado = tiempo_actual
        else:
            sprites.draw(SCREEN)
            dibujar_victoria(nivel, tiempo_ganado)
            # Al tocar/clic se cambia ganado=False arriba; aquí hacemos el reset
            if not ganado:
                nivel += 1
                paredes, rects_paredes, powerups = nuevo_nivel()
                jugador.rects_paredes  = rects_paredes
                jugador.hitbox.center  = (INICIO_X, INICIO_Y)
                jugador.direction      = "ABJ_F"
                tiempo_inicio          = pg.time.get_ticks()
                tiempo_ganado          = 0

        pg.display.flip()

    pg.quit()
    sys.exit()

if __name__ == "__main__":
    main()
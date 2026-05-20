from math import floor as mfloor
import numpy as np
from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
from ursina import Audio
from noise import pnoise2, pnoise3

app = Ursina()

DirectionalLight(shadows=False, rotation=(45, -45, 45), color=color.rgb(220, 220, 200))
camera.fov = 90
window.color = color.rgb(70, 216, 255)

sound_place = Audio('Block.mp3', loop=False, autoplay=False)
sound_break = Audio('Block.mp3', loop=False, autoplay=False)

# ========================
# CONSTANTES
# ========================
MIN_Y        = 0      # piso absoluto del mundo
MAX_Y        = 40     # techo absoluto (evita colocar bloques en el aire infinito)
REACH        = 6      # distancia máxima de interacción
COOLDOWN     = 0.15   # segundos mínimos entre acciones (evita clicks dobles)

# ========================
# INVENTARIO
# ========================
current_texture = 'grass.png'
selected_index  = '7'

textures = {
    '1': 'wood.png',
    '2': 'log.png',
    '3': 'sand.png',
    '4': 'stone.png',
    '5': 'leaves.png',
    '6': 'web.png',
    '7': 'grass.png',
    '8': 'BedRock.png',
    '9': 'brick.png',
}

inventory_ui = []

def create_inventory_ui():
    for i, (key, tex) in enumerate(textures.items(), start=1):
        btn = Button(
            parent=camera.ui,
            model='quad',
            texture=tex,
            scale=0.15,
            position=Vec2(-0.9 + i * 0.2, -0.45),
        )
        inventory_ui.append((key, btn))
    update_inventory_ui()

def update_inventory_ui():
    for key, btn in inventory_ui:
        btn.color = color.white if key == selected_index else color.gray

# ========================
# DATOS DEL MUNDO
# ========================
world_data = {}

chunk_size   = 5
chunk_radius = 1
active_chunks = {}
player_current_chunk = None
height_cache = {}

# ========================
# RAYCAST PROPIO — ROBUSTO
# ========================
# Motivo: hit.world_point de Ursina en bordes exactos de cara
# puede redondearse mal por float point → bloque equivocado.
# Esta función avanza paso a paso por el rayo y devuelve
# las coordenadas exactas de world_data.
#
# Retorna: (bloque_objetivo, bloque_anterior)
#   bloque_objetivo → el que se rompe  (None si no hay nada)
#   bloque_anterior → donde se coloca  (None si no hay espacio previo)
# ========================
def voxel_raycast(step_break=0.05, step_highlight=0.1, for_highlight=False):
    step = step_highlight if for_highlight else step_break
    steps = int(REACH / step)

    pos = Vec3(camera.world_position)
    fwd = camera.forward.normalized()
    prev = None

    for _ in range(steps):
        pos += fwd * step
        curr = (int(mfloor(pos.x)), int(mfloor(pos.y)), int(mfloor(pos.z)))

        if curr in world_data:
            return curr, prev   # (bloque a romper, posición para colocar)
        prev = curr

    return None, None

# ========================
# GENERACION DE TERRENO
# ========================
def get_chunk_coords(pos):
    return Vec2(int(pos.x // chunk_size), int(pos.z // chunk_size))

def generate_height(x, z):
    if (x, z) not in height_cache:
        height_cache[(x, z)] = int(pnoise2(x * 0.05, z * 0.05, octaves=1) * 5 + 7)
    return height_cache[(x, z)]

def is_cave(x, y, z):
    return pnoise3(x * 0.08, y * 0.08, z * 0.08, octaves=1) > 0.2

def get_block_type(y, height):
    if y == 0:
        return 'BedRock.png'       # capa de bedrock
    if y == height - 1:
        if height < 5:  return 'sand.png'
        if height > 9:  return 'stone.png'
        return 'grass.png'
    if y > height - 4:
        return 'dirt.png'
    return 'stone.png'

def is_air(x, y, z):
    return (x, y, z) not in world_data

# ========================
# CHUNKS
# ========================
def load_chunk(cx, cz):
    # 1) poblar world_data
    for x in range(cx * chunk_size, (cx + 1) * chunk_size):
        for z in range(cz * chunk_size, (cz + 1) * chunk_size):
            height = generate_height(x, z)
            for y in range(height):
                if is_cave(x, y, z) and y > 0:   # nunca cueva en y=0 (bedrock)
                    continue
                if (x, y, z) not in world_data:
                    world_data[(x, y, z)] = get_block_type(y, height)

    # 2) construir geometría
    face_data  = {}
    coll_verts = []
    coll_tris  = []
    coll_idx   = 0

    def add_face(tex, v0, v1, v2, v3):
        nonlocal coll_idx
        if tex not in face_data:
            face_data[tex] = {'vertices': [], 'triangles': [], 'uvs': [], 'index': 0}
        d = face_data[tex]
        i = d['index']
        d['vertices'].extend([v0, v1, v2, v3])
        d['triangles'].extend([i, i+1, i+2, i, i+2, i+3])
        d['uvs'].extend([(0,0),(1,0),(1,1),(0,1)])
        d['index'] += 4

        coll_verts.extend([v0, v1, v2, v3])
        coll_tris.extend([coll_idx, coll_idx+1, coll_idx+2,
                          coll_idx, coll_idx+2, coll_idx+3])
        coll_idx += 4

    for x in range(cx * chunk_size, (cx + 1) * chunk_size):
        for z in range(cz * chunk_size, (cz + 1) * chunk_size):
            height = generate_height(x, z)
            for y in range(height):
                if (x, y, z) not in world_data:
                    continue
                tex = world_data[(x, y, z)]
                lx  = x - cx * chunk_size
                lz  = z - cz * chunk_size

                if is_air(x, y+1, z): add_face(tex, Vec3(lx,y+1,lz),   Vec3(lx+1,y+1,lz),   Vec3(lx+1,y+1,lz+1), Vec3(lx,y+1,lz+1))
                if is_air(x, y-1, z): add_face(tex, Vec3(lx,y,lz),     Vec3(lx,y,lz+1),     Vec3(lx+1,y,lz+1),   Vec3(lx+1,y,lz))
                if is_air(x+1, y, z): add_face(tex, Vec3(lx+1,y,lz),   Vec3(lx+1,y,lz+1),   Vec3(lx+1,y+1,lz+1), Vec3(lx+1,y+1,lz))
                if is_air(x-1, y, z): add_face(tex, Vec3(lx,y,lz),     Vec3(lx,y+1,lz),     Vec3(lx,y+1,lz+1),   Vec3(lx,y,lz+1))
                if is_air(x, y, z+1): add_face(tex, Vec3(lx,y,lz+1),   Vec3(lx,y+1,lz+1),   Vec3(lx+1,y+1,lz+1), Vec3(lx+1,y,lz+1))
                if is_air(x, y, z-1): add_face(tex, Vec3(lx,y,lz),     Vec3(lx+1,y,lz),     Vec3(lx+1,y+1,lz),   Vec3(lx,y+1,lz))

    entities = []
    pos = Vec3(cx * chunk_size, 0, cz * chunk_size)

    for tex, d in face_data.items():
        if not d['vertices']:
            continue
        mesh = Mesh(vertices=d['vertices'], triangles=d['triangles'], uvs=d['uvs'])
        mesh.generate_normals()
        entities.append(Entity(model=mesh, texture=tex, position=pos))

    # Un solo collider invisible por chunk
    if coll_verts:
        coll_mesh = Mesh(vertices=coll_verts, triangles=coll_tris)
        entities.append(Entity(model=coll_mesh, collider='mesh', visible=False, position=pos))

    return entities

def unload_chunk(voxels):
    for v in voxels:
        destroy(v)

def rebuild_chunk(cx, cz):
    """Solo reconstruye si el chunk está cargado actualmente."""
    key = Vec2(cx, cz)
    if key in active_chunks:
        unload_chunk(active_chunks[key])
        active_chunks[key] = load_chunk(cx, cz)

def rebuild_affected_chunks(bx, bz):
    """Reconstruye solo los chunks que realmente pueden verse afectados."""
    cx = int(mfloor(bx / chunk_size))
    cz = int(mfloor(bz / chunk_size))
    lx = bx - cx * chunk_size
    lz = bz - cz * chunk_size

    rebuild_chunk(cx, cz)
    if lx == 0:               rebuild_chunk(cx - 1, cz)
    if lx == chunk_size - 1:  rebuild_chunk(cx + 1, cz)
    if lz == 0:               rebuild_chunk(cx, cz - 1)
    if lz == chunk_size - 1:  rebuild_chunk(cx, cz + 1)

def update_chunks():
    global player_current_chunk
    pc = get_chunk_coords(player.position)
    if pc == player_current_chunk:
        return

    new_active = {}
    for dx in range(-chunk_radius, chunk_radius + 1):
        for dz in range(-chunk_radius, chunk_radius + 1):
            key = Vec2(pc.x + dx, pc.y + dz)
            if key not in active_chunks:
                active_chunks[key] = load_chunk(int(key.x), int(key.y))
            new_active[key] = active_chunks[key]

    for key in list(active_chunks.keys()):
        if key not in new_active:
            unload_chunk(active_chunks[key])
            del active_chunks[key]

    player_current_chunk = pc

# ========================
# VALIDACIONES DE BLOQUE
# ========================
def is_indestructible(bx, by, bz):
    """Bloques que no se pueden romper (bedrock en y=0)."""
    if by <= MIN_Y:
        return True
    if world_data.get((bx, by, bz)) == 'BedRock.png' and by == 0:
        return True
    return False

def is_valid_place_position(px, py, pz):
    """
    Verifica si una posición es válida para colocar un bloque.
    Falla si:
      - ya hay un bloque ahí
      - está fuera de rango Y
      - está dentro del cuerpo del jugador
    """
    # Ya existe un bloque
    if (px, py, pz) in world_data:
        return False

    # Fuera de rango vertical
    if py < MIN_Y or py > MAX_Y:
        return False

    # Colisión con el jugador
    # El jugador ocupa aproximadamente 2 bloques de alto
    px_p = int(mfloor(player.position.x))
    py_p = int(mfloor(player.position.y))
    pz_p = int(mfloor(player.position.z))

    player_blocks = {
        (px_p,     py_p,     pz_p),
        (px_p,     py_p + 1, pz_p),
    }
    if (px, py, pz) in player_blocks:
        return False

    return True

# ========================
# ACCIONES PRINCIPALES
# ========================
last_action_time = 0.0

def try_break_block():
    target, _ = voxel_raycast()
    if target is None:
        return

    bx, by, bz = target

    # Verificar que realmente existe en world_data (puede ser posición de cueva)
    if (bx, by, bz) not in world_data:
        return

    # Bloque indestructible
    if is_indestructible(bx, by, bz):
        return

    del world_data[(bx, by, bz)]
    sound_break.play()
    rebuild_affected_chunks(bx, bz)

def try_place_block():
    target, place = voxel_raycast()

    # Necesitamos tanto el bloque objetivo como la posición adyacente
    if target is None or place is None:
        return

    px, py, pz = place

    if not is_valid_place_position(px, py, pz):
        return

    world_data[(px, py, pz)] = current_texture
    sound_place.play()
    rebuild_affected_chunks(px, pz)

# ========================
# INPUT
# ========================
def input(key):
    global selected_index, current_texture, last_action_time

    if key in textures:
        selected_index = key
        current_texture = textures[key]
        update_inventory_ui()
        return

    # Cooldown entre acciones para evitar doble click y spam
    now = time.time()
    if now - last_action_time < COOLDOWN:
        return
    last_action_time = now

    if key == 'left mouse down':
        try_break_block()

    elif key == 'right mouse down':
        try_place_block()

# ========================
# PLAYER
# ========================
player = FirstPersonController(position=(5, 40, 5), speed=5)
player.gravity = 0.5

# Highlight del bloque apuntado
highlight = Entity(
    model='cube',
    color=color.rgba(0, 0, 0, 0),
    scale=1.01,
    enabled=False
)
Entity(
    parent=highlight,
    model='cube',
    color=color.black,
    scale=1.02,
    wireframe=True
)

def update():
    update_chunks()

    # Usar paso más grande para el highlight (no necesita precisión de click)
    target, _ = voxel_raycast(for_highlight=True)

    if target is not None and target in world_data:
        highlight.position = Vec3(target[0], target[1], target[2])
        highlight.enabled = True
    else:
        highlight.enabled = False

create_inventory_ui()
app.run()

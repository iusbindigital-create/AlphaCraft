import numpy as np
from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController

app = Ursina()

# Color del cielo
color_sky = color.rgb(50, 50, 235)
sky = Entity(model='sphere', scale=500, color=color_sky, double_sided=True)

# Texturas y manejo de inventario
current_texture = 'grass.png'  # Textura inicial

textures = {
    '1': 'wood.png',
    '2': 'log.png',
    '3': 'sand.png',
    '4': 'stone.png',
    '5': 'leaves.png',
    '6': 'web.png',
    '7': 'grass.png',
    '8': 'BedRock.png',
    '9': 'brick.png'
}

def set_current_texture(texture):
    global current_texture
    current_texture = texture

# Función para obtener coordenadas de chunk
def get_chunk_coords(position, chunk_size=5):
    return (int(position.x // chunk_size), int(position.z // chunk_size))

# Diccionario de chunks cargados
active_chunks = {}
chunk_size = 5
chunk_radius = 1  # Ajustable para optimizar rendimiento

class Voxel(Button):
    def __init__(self, position=(0,0,0), texture='grass.png'):
        super().__init__(
            parent=scene,
            position=position,
            model='cube',
            origin_y=0.5,
            texture=texture,
            color=color.white,
            collider='box'
        )

    def input(self, key):
        if self.hovered:
            if key == "right mouse down":
                Voxel(position=self.position + Vec3(0,1,0), texture=current_texture)
            elif key == "left mouse down":
                destroy(self)

# Generación del terreno optimizada
def generate_height(x, z):
    """Genera la altura del terreno usando ruido Perlin."""
    return int(np.sin(x * 0.1) * np.cos(z * 0.1) * 3 + 3)

# Cargar chunks dinámicamente
def load_chunk(cx, cz):
    """Genera un chunk de 5x5 con variaciones de altura."""
    chunk_voxels = []
    for x in range(cx * chunk_size, (cx + 1) * chunk_size):
        for z in range(cz * chunk_size, (cz + 1) * chunk_size):
            height = generate_height(x, z)
            for y in range(height):
                texture = 'stone.png' if y < height - 1 else 'grass.png'
                voxel = Voxel(position=(x, y, z), texture=texture)
                chunk_voxels.append(voxel)
    return chunk_voxels

# Descargar un chunk
def unload_chunk(chunk_voxels):
    """Elimina todos los bloques de un chunk."""
    for voxel in chunk_voxels:
        destroy(voxel)

# Control de actualización de chunks
player_current_chunk = None

def update_chunks():
    global player_current_chunk
    player_chunk = get_chunk_coords(player.position)

    if player_chunk != player_current_chunk:
        new_active = {}
        
        # Cargar solo los chunks necesarios
        for cx in range(player_chunk[0] - chunk_radius, player_chunk[0] + chunk_radius + 1):
            for cz in range(player_chunk[1] - chunk_radius, player_chunk[1] + chunk_radius + 1):
                key = (cx, cz)
                if key not in active_chunks:
                    active_chunks[key] = load_chunk(cx, cz)
                new_active[key] = active_chunks[key]

        # Descargar los chunks que ya no están cerca del jugador
        for key in list(active_chunks.keys()):
            if key not in new_active:
                unload_chunk(active_chunks[key])
                del active_chunks[key]

        player_current_chunk = player_chunk

# Función update principal
def update():
    update_chunks()

# Crear jugador
player = FirstPersonController(position=Vec3(5, 25, 5), speed=5)

app.run()

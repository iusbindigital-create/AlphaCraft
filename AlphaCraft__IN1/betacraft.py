import numpy as np
from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController

app = Ursina()

# Color del cielo
color_sky = color.rgb(50, 50, 235)
sky = Entity(model='sphere', scale=500, color=color_sky, double_sided=True)

# Creamos un contenedor para el inventario
inventory_slots = []
current_texture = 'brick'  # Textura seleccionada por defecto

textures = {
    '2': 'wood.png',
    '3': 'log.png',
    '4': 'sand.png',
    '5': 'stone.png',
    '6': 'leaves.png',
    '7': 'web.png',
    '8': 'grass.png',
    '9': 'BedRock.png'
}

# Crear las ranuras del inventario
for i, texture in enumerate(textures.values()):
    slot = Button(
        parent=camera.ui,
        position=Vec2(-0.8 + i * 0.2, -0.4),
        model='quad',
        texture=texture,
        scale=(0.1, 0.1),
        color=color.white,
        on_click=lambda texture=texture: set_current_texture(texture)  # Establecer textura seleccionada
    )
    inventory_slots.append(slot)

highlight = Entity(
    parent=camera.ui,
    model='quad',
    scale=(0.12, 0.12),
    color=color.yellow,
    visible=False,
    z=-1  # Asegúrate de que se dibuje sobre otras entidades UI
)


def set_current_texture(texture):
    global current_texture
    current_texture = texture
    # Mostrar el resalto en la ranura seleccionada
    for i, slot in enumerate(inventory_slots):
        if slot.texture == texture:
            highlight.position = slot.position
            highlight.visible = True
            break

# Textura por defecto
set_current_texture('brick')

class Voxel(Button):
    def __init__(self, position=(0, 0, 0), texture='brick'):
        super().__init__(
            parent=scene,
            position=position,
            model='cube',
            origin_y=0.5,
            texture=texture,
            color=color.white,
            collider='box'
        )
        self.is_wall = texture == 'BedRock.png'

        # Verificar si las caras adyacentes son visibles
        self.update_faces()

    def update_faces(self):
        """Actualiza las caras visibles del voxel."""
        if self.check_adjacent(Vec3(1, 0, 0)):  # Lado derecho
            self.model = 'cube'  # No se renderiza la cara derecha
        if self.check_adjacent(Vec3(-1, 0, 0)):  # Lado izquierdo
            self.model = 'cube'  # No se renderiza la cara izquierda
        if self.check_adjacent(Vec3(0, 1, 0)):  # Arriba
            self.model = 'cube'  # No se renderiza la cara superior
        if self.check_adjacent(Vec3(0, -1, 0)):  # Abajo
            self.model = 'cube'  # No se renderiza la cara inferior
        if self.check_adjacent(Vec3(0, 0, 1)):  # Lado de frente
            self.model = 'cube'  # No se renderiza la cara del frente
        if self.check_adjacent(Vec3(0, 0, -1)):  # Lado posterior
            self.model = 'cube'  # No se renderiza la cara posterior

    def check_adjacent(self, direction):
        """Verifica si hay un bloque adyacente en la dirección dada."""
        adjacent_position = self.position + direction
        for voxel in scene.entities:
            if isinstance(voxel, Voxel) and voxel.position == adjacent_position:
                return True  # Hay un bloque adyacente
        return False  # No hay un bloque adyacente

    def input(self, key):
        if self.hovered:
            if key == "right mouse down":
                if not self.is_wall:
                    Voxel(position=self.position + Vec3(0, 1, 0), texture=current_texture)
            elif key == "left mouse down":
                if not self.is_wall:
                    destroy(self)

def perlin_noise(x, z, scale=10):
    return np.sin(x / scale) * np.cos(z / scale)

def generate_height(x, z):
    height = perlin_noise(x, z, scale=10)
    return int((height + 1) * 3)

def create_terrain(chunk_size):
    for z in range(chunk_size):
        for x in range(chunk_size):
            height = generate_height(x, z)
            for y in range(height):
                Voxel(position=(x, y, z), texture='grass.png')

    wall_height = 20
    for x in range(chunk_size):
        for y in range(wall_height):
            Voxel(position=(x, y, 0), texture='BedRock.png')
            Voxel(position=(x, y, chunk_size - 1), texture='BedRock.png')
    for z in range(chunk_size):
        for y in range(wall_height):
            Voxel(position=(0, y, z), texture='BedRock.png')
            Voxel(position=(chunk_size - 1, y, z), texture='BedRock.png')

chunkSize = 24
create_terrain(chunkSize)

player_start_position = Vec3(chunkSize / 2, 5, chunkSize / 2)
player = FirstPersonController(position=player_start_position, speed=5)

# Detectar las teclas presionadas para cambiar la textura
def update():
    global current_texture
    # Cambiar la textura seleccionada con las teclas numéricas
    if held_keys['1']:
        current_texture = 'wood.png'
        set_current_texture(current_texture)
    elif held_keys['2']:
        current_texture = 'log.png'
        set_current_texture(current_texture)
    elif held_keys['3']:
        current_texture = 'sand.png'
        set_current_texture(current_texture)
    elif held_keys['4']:
        current_texture = 'stone.png'
        set_current_texture(current_texture)
    elif held_keys['5']:
        current_texture = 'leaves.png'
        set_current_texture(current_texture)
    elif held_keys['6']:
        current_texture = 'web.png'
        set_current_texture(current_texture)
    elif held_keys['7']:
        current_texture = 'grass.png'
        set_current_texture(current_texture)
    elif held_keys['8']:
        current_texture = 'BedRock.png'
        set_current_texture(current_texture)
    elif held_keys['9']:
        current_texture = 'brick.png'
        set_current_texture(current_texture)

app.run()

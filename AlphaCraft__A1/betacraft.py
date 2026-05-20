from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController

app = Ursina()

class Voxel(Button):
    def __init__(self, position=(0,0,0), texture='brick'):
        super().__init__(
            parent=scene,
            position=position,
            model='cube',
            origin_y=0.5,
            texture=texture,
            color=color.white,  # Usar color blanco por defecto
            highlight_color=color.lime,  # Color de resaltado cuando el ratón está sobre el voxel
            collider='box'  # Añadir colisión para que el voxel sea interactivo
        )

    def input(self, key):
        if self.hovered:
            if key == "left mouse down":
                voxel_position = mouse.world_point
                voxel_position = Vec3(round(voxel_position.x), round(voxel_position.y), round(voxel_position.z))
                Voxel(position=voxel_position + Vec3(0, 1, 0), texture='brick')
            elif key == "right mouse down":
                destroy(self)

def create_terrain(chunk_size, height):
    for z in range(chunk_size):
        for x in range(chunk_size):
            for y in range(height):
                Voxel(position=(x, y, z), texture='grass')

# Reducir el tamaño del terreno para mejorar el rendimiento
chunkSize = 16
terrainHeight = 5

create_terrain(chunkSize, terrainHeight)

# Ajustar la posición inicial del jugador para que esté sobre el terreno
player = FirstPersonController(position=(chunkSize / 2, terrainHeight + 2, chunkSize / 2))  # Colocar al jugador en el centro del terreno y por encima

app.run()

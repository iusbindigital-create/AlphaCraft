from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController

app = Ursina()

class Voxel(Button):
    def __init__(self, position=(0,0,0)):
        super().__init__(
            parent=scene,
            position=position,
            model='cube',
            origin_y=0.5,
            texture='grass',
            color=color.rgb(255,255,255),
            highlight_color=color.lime,
        )

    def input(self, key):
        if self.hovered:
            if key == "left mouse down":
                # Obtener la posición del mouse en el mundo
                voxel_position = mouse.world_point
                
                # Ajustar la posición para que esté en una altura correcta sobre el bloque existente
                voxel_position = Vec3(round(voxel_position.x), round(voxel_position.y), round(voxel_position.z))
                Voxel(position=voxel_position + Vec3(0, 1, 0))
            elif key == "right mouse down":
                destroy(self)

# Crear el terreno de bloques
chunkSize = 16
for z in range(chunkSize):
    for x in range(chunkSize):
        voxel = Voxel(position=(x, 0, z))

player = FirstPersonController()

app.run()

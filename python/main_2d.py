from __future__ import annotations

from typing import Any
import time

import wgpu
from rendercanvas.glfw import RenderCanvas, loop

from camera2d import *
from colormaterial import *
from transform import *
from quad import *
from texture import *
from sampler import *
from textureset import *
from node import *
from shader import *
from pipeline import *
from scene import *
from renderer import *
from engine import *

canvas: RenderCanvas
device: wgpu.GPUDevice
context: Any
renderer: Renderer
camera: Camera2D
scene: Scene
last_t: float = 0.0

class Rotate(Engine):
  def __init__ (self, trf: Transform, speed: float) -> None:
    self.trf = trf
    self.speed = speed
  def update (self, dt: float) -> None:
    self.trf.rotate(self.speed * dt, 0, 0, 1)

def make_body (quad: Quad, textures: TextureSet, material: ColorMaterial, size: float) -> Node:
  trf = Transform()
  trf.translate(-size / 2, -size / 2, 0)
  trf.scale(size, size, 1)
  return Node(trf=trf, apps=[material, textures], shps=[quad])

def initialize (device: wgpu.GPUDevice, target_format: str) -> None:
  # create objects
  global camera
  camera = Camera2D(0, 16, 0, 12)

  quad = Quad(device)
  background_texture = Texture(device, "decal_texture", "../images/space.png")
  sun_texture = Texture(device, "decal_texture", "../images/Sun.png")
  earth_texture = Texture(device, "decal_texture", "../images/earth.jpg")
  moon_texture = Texture(device, "decal_texture", "../images/moon.png")
  venus_texture = Texture(device, "decal_texture", "../images/venus.png")
  sampler = Sampler(device, "decal_sampler")
  background_set = TextureSet([background_texture, sampler])
  sun_set = TextureSet([sun_texture, sampler])
  earth_set = TextureSet([earth_texture, sampler])
  moon_set = TextureSet([moon_texture, sampler])
  venus_set = TextureSet([venus_texture, sampler])
  white_material = ColorMaterial(1, 1, 1)
  round_material = ColorMaterial(1, 1, 1)
  round_material.set("round", 1.0)

  shader = Shader(device, "../shaders/2d/shader.wgsl")
  shader.set_vertex_buffers([
    {"array_stride": 2 * 4, "step_mode": "vertex",
     "attributes": [{"format": "float32x2", "offset": 0, "var_name": "pos"}]},
    {"array_stride": 2 * 4, "step_mode": "vertex",
     "attributes": [{"format": "float32x2", "offset": 0, "var_name": "texcoord"}]},
  ])
  pipeline = Pipeline(shader, target_format, depth_stencil=None)
  shader.add_material(white_material)
  shader.add_material(round_material)
  for texture_set in (background_set, sun_set, earth_set, moon_set, venus_set):
    shader.add_texture_set(texture_set)

  background = Transform()
  background.scale(16, 12, 1)
  background_node = Node(trf=background, apps=[background_set], shps=[quad])

  sun_anchor = Transform()
  sun_anchor.translate(8, 6, 0)
  sun = Node(trf=sun_anchor,
             nodes=[make_body(quad, sun_set, round_material, 2.4)])

  mercury_orbit = Transform()
  mercury_orbit.translate(8, 6, 0)
  mercury_distance = Transform()
  mercury_distance.translate(1.9, 0, 0)
  mercury_node = Node(trf=mercury_distance,
                      nodes=[make_body(quad, venus_set, round_material, 0.65)])
  mercury_system = Node(trf=mercury_orbit, nodes=[mercury_node])

  earth_orbit = Transform()
  earth_orbit.translate(8, 6, 0)
  earth_system = Transform()
  earth_system.translate(4.0, 0, 0)
  earth_axis = Transform()
  earth_node = Node(trf=earth_axis,
                    nodes=[make_body(quad, earth_set, round_material, 1.1)])

  moon_orbit = Transform()
  moon_distance = Transform()
  moon_distance.translate(1.35, 0, 0)
  moon_node = Node(trf=moon_distance,
                   nodes=[make_body(quad, moon_set, round_material, 0.5)])
  moon_system = Node(trf=moon_orbit, nodes=[moon_node])
  earth_group = Node(trf=earth_system, nodes=[earth_node, moon_system])
  earth_system_node = Node(trf=earth_orbit, nodes=[earth_group])

  # build scene
  root = Node(pipeline, apps=[white_material],
              nodes=[background_node, sun, mercury_system, earth_system_node])
  global scene
  scene = Scene(root)
  scene.add_engine(Rotate(mercury_orbit, 45.0))
  scene.add_engine(Rotate(earth_orbit, 20.0))
  scene.add_engine(Rotate(earth_axis, 120.0))
  scene.add_engine(Rotate(moon_orbit, 80.0))

def update (dt: float) -> None:
  scene.update(dt)

def draw () -> None:
  global last_t
  t = time.perf_counter()
  update(t - last_t)
  last_t = t

  target_texture = context.get_current_texture()
  renderer.render(target_texture, scene, camera)

def on_key (event: Any) -> None:
  if event["key"] == "q":
    canvas.close()

def main () -> None:
  global canvas, device, context, renderer, last_t

  canvas = RenderCanvas(size=(600, 600), title="2D scene", update_mode="continuous", max_fps=60)
  adapter = wgpu.gpu.request_adapter_sync()
  device = adapter.request_device_sync()
  context = canvas.get_context("wgpu")
  # formato preferido COM "-srgb": a GPU codifica de linear para sRGB
  # automaticamente na saída — correto desde que o shader faça a conta de
  # iluminação em espaço linear.
  target_format = context.get_preferred_format(device.adapter)
  context.configure(device=device, format=target_format)

  renderer = Renderer(device, clear_value=(0.0, 0.0, 0.0, 1.0))

  initialize(device, target_format)

  canvas.add_event_handler(on_key, "key_down")
  last_t = time.perf_counter()
  canvas.request_draw(draw)
  loop.run()

if __name__ == "__main__":
  main()

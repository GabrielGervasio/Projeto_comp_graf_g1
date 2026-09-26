struct Matrix {
  vertex: mat4x4<f32>,       // objeto -> espaco global (2D nao ilumina)
}
@group(0) @binding(0) var<storage, read> matrix: array<Matrix>;

struct Global {
  projection: mat4x4<f32>,   // espaco de iluminacao -> NDC
}
@group(2) @binding(0) var<uniform> global: Global;


struct ColorBlock {
  color: vec3<f32>,
  opacity: f32,
  round: f32,
}
@group(1) @binding(0) var<uniform> material: ColorBlock;

@group(3) @binding(0) var decal_texture: texture_2d<f32>;
@group(3) @binding(1) var decal_sampler: sampler;

struct VertexOutput {
  @builtin(position) clip_position: vec4<f32>,
  @location(0) texcoord: vec2<f32>,
}

@vertex
fn vs_main (@builtin(instance_index) instance_index: u32,
            @location(0) pos: vec2<f32>,
            @location(1) texcoord: vec2<f32>) -> VertexOutput {
  var out: VertexOutput;
  out.clip_position = global.projection * (matrix[instance_index].vertex * vec4<f32>(pos, 0.0, 1.0));
  out.texcoord = texcoord;
  return out;
}

@fragment
fn fs_main (in: VertexOutput) -> @location(0) vec4<f32> {
  if (material.round > 0.5 && distance(in.texcoord, vec2<f32>(0.5, 0.5)) > 0.5) {
    discard;
  }
  return textureSample(decal_texture, decal_sampler, in.texcoord) *
         vec4<f32>(material.color, material.opacity);
}

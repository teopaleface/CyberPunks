import { useEffect, useRef } from "react"
import { prefersReducedMotion } from "@/lib/motion"
import { cn } from "@/lib/utils"

/**
 * Energy beam drawn with one WebGL fragment shader, matching the reference
 * frame from the brief: a white-hot dome at the bottom, concentric orange
 * arcs rippling out of it, and a thin flickering beam climbing to the top.
 * The pointer tilts the beam a little. Pauses off screen; under reduced
 * motion it renders a single still frame.
 */

const VERT = `
attribute vec2 p;
void main(){ gl_Position = vec4(p, 0.0, 1.0); }
`

const FRAG = `
precision highp float;
uniform vec2 uRes;
uniform float uTime;
uniform vec2 uMouse;

float hash(vec2 p){ return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float noise(float x){ float i = floor(x); float f = fract(x); return mix(hash(vec2(i, 0.0)), hash(vec2(i + 1.0, 0.0)), smoothstep(0.0, 1.0, f)); }

void main(){
  vec2 frag = gl_FragCoord.xy;
  float H = uRes.y;
  // dome centre sits just below the bottom edge, in the middle
  vec2 c = vec2(uRes.x * 0.5, -H * 0.05);
  vec2 p = (frag - c) / H;
  float t = uTime;

  float R = 0.19;                 // dome radius
  float d = length(p);
  float above = smoothstep(-0.02, 0.06, p.y + 0.02);

  // white-hot dome and its halo
  float dome = 1.0 - smoothstep(R - 0.012, R + 0.004, d);
  float halo = exp(-max(d - R, 0.0) * 14.0) * 0.8;
  float rim  = exp(-abs(d - R) * 90.0);

  // concentric arcs rippling outward
  float k = (d - R);
  float arcs = 0.5 + 0.5 * cos((k - t * 0.03) * 120.0);
  arcs = pow(arcs, 4.0);
  float arcMask = exp(-max(k, 0.0) * 5.5) * smoothstep(0.0, 0.02, k);
  // arcs fade toward the sides, strongest straight up
  float ang = abs(atan(p.x, p.y));
  float spread = exp(-ang * ang * 1.3);
  float rings = arcs * arcMask * spread * above;

  // the beam: thin core + soft glow, flickering, slightly tilted by the pointer
  float y = p.y;
  float bx = p.x - (uMouse.x - 0.5) * 0.06 * y;
  float flick = 0.75 + 0.25 * noise(t * 6.0) + 0.15 * sin(y * 30.0 - t * 9.0);
  float w = mix(0.007, 0.0016, smoothstep(0.0, 1.0, y));
  float beamCore = exp(-abs(bx) / w);
  float beamGlow = exp(-abs(bx) / (w * 8.0)) * 0.3;
  float beamLen = (1.0 - smoothstep(0.15, 1.05, y)) * smoothstep(R - 0.05, R + 0.05, y);
  float beam = (beamCore + beamGlow) * beamLen * flick;

  // a soft pulse travelling up the beam
  float pulse = exp(-pow((y - fract(t * 0.22) * 1.2) * 9.0, 2.0)) * beamCore * beamLen;

  float lens = 0.55 + 1.25 * smoothstep(R * 0.5, R, d);
  float I = dome * lens * 1.5 + halo * 0.5 + rim * 0.8 + rings * 0.75 + beam * 1.1 + pulse * 0.7;

  vec3 col = vec3(0.0);
  // palette: magenta (255,92,255) at the edge, amber (255,197,2) toward the core, white at the core
  col += vec3(0.62, 0.22, 0.62) * smoothstep(0.02, 0.45, I);
  col += vec3(0.38, 0.55, -0.61) * smoothstep(0.45, 1.25, I);
  col += vec3(0.00, 0.23, 0.99) * smoothstep(1.4, 2.3, I);
  // a cool hint inside the dome, as in the reference
  col = mix(col, col * vec3(0.85, 0.85, 1.05), dome * 0.35);

  // vignette and grain
  float vig = 1.0 - smoothstep(0.25, 1.35, length((frag / uRes - vec2(0.5, 0.25)) * vec2(1.4, 1.0)));
  col *= vig;
  col += (hash(frag + t) - 0.5) * 0.02;

  gl_FragColor = vec4(col, 1.0);
}
`

export function EnergyBeamShader({ className }: { className?: string }) {
  const canvasRef = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const gl = canvas.getContext("webgl", { antialias: false, premultipliedAlpha: false })
    if (!gl) return

    const compile = (type: number, src: string) => {
      const s = gl.createShader(type)!
      gl.shaderSource(s, src)
      gl.compileShader(s)
      if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) console.error(gl.getShaderInfoLog(s))
      return s
    }
    const prog = gl.createProgram()!
    gl.attachShader(prog, compile(gl.VERTEX_SHADER, VERT))
    gl.attachShader(prog, compile(gl.FRAGMENT_SHADER, FRAG))
    gl.linkProgram(prog)
    gl.useProgram(prog)

    const buf = gl.createBuffer()
    gl.bindBuffer(gl.ARRAY_BUFFER, buf)
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW)
    const loc = gl.getAttribLocation(prog, "p")
    gl.enableVertexAttribArray(loc)
    gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0)

    const uRes = gl.getUniformLocation(prog, "uRes")
    const uTime = gl.getUniformLocation(prog, "uTime")
    const uMouse = gl.getUniformLocation(prog, "uMouse")

    const reduce = prefersReducedMotion()
    const mouse = { x: 0.5, y: 0.5, tx: 0.5, ty: 0.5 }
    let visible = true
    let raf = 0
    const start = performance.now()

    const resize = () => {
      const dpr = Math.min(window.devicePixelRatio || 1, 1.5)
      const w = canvas.clientWidth,
        h = canvas.clientHeight
      canvas.width = Math.max(1, Math.round(w * dpr))
      canvas.height = Math.max(1, Math.round(h * dpr))
      gl.viewport(0, 0, canvas.width, canvas.height)
      if (reduce) render(0)
    }
    const ro = new ResizeObserver(() => resize())
    const io = new IntersectionObserver(([e]) => (visible = e.isIntersecting))
    io.observe(canvas)

    const onMove = (e: PointerEvent) => {
      mouse.tx = e.clientX / window.innerWidth
      mouse.ty = e.clientY / window.innerHeight
    }
    window.addEventListener("pointermove", onMove, { passive: true })

    const render = (now: number) => {
      mouse.x += (mouse.tx - mouse.x) * 0.05
      mouse.y += (mouse.ty - mouse.y) * 0.05
      gl.uniform2f(uRes, canvas.width, canvas.height)
      gl.uniform1f(uTime, reduce ? 4 : (now - start) / 1000)
      gl.uniform2f(uMouse, mouse.x, mouse.y)
      gl.drawArrays(gl.TRIANGLES, 0, 3)
    }

    resize()
    ro.observe(canvas)

    const loop = (now: number) => {
      raf = requestAnimationFrame(loop)
      if (visible) render(now)
    }
    if (reduce) render(0)
    else raf = requestAnimationFrame(loop)

    return () => {
      cancelAnimationFrame(raf)
      ro.disconnect()
      io.disconnect()
      window.removeEventListener("pointermove", onMove)
    }
  }, [])

  return <canvas ref={canvasRef} aria-hidden className={cn("block h-full w-full bg-black", className)} />
}

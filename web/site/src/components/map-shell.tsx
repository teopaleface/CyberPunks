import { useEffect, type ReactNode } from "react"
import { TileLayer, useMap } from "react-leaflet"
import { cn } from "@/lib/utils"

const ESRI = "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas"
const ATTRIBUTION = "Tiles &copy; Esri, HERE, Garmin, &copy; OpenStreetMap contributors"

/** A schematic dark map: grey land and water, roads as thin lines, labels on top. No key needed. */
export function SchematicTiles() {
  return (
    <>
      <TileLayer url={`${ESRI}/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}`} attribution={ATTRIBUTION} maxZoom={16} />
      <TileLayer url={`${ESRI}/World_Dark_Gray_Reference/MapServer/tile/{z}/{y}/{x}`} maxZoom={16} />
      <CtrlWheelZoom />
    </>
  )
}

/**
 * The plain wheel scrolls the page, even with the pointer over the map;
 * Ctrl (or a trackpad pinch, which arrives as Ctrl + wheel) zooms the map.
 * The +/- buttons and a double click zoom too.
 */
function CtrlWheelZoom() {
  const map = useMap()
  useEffect(() => {
    map.scrollWheelZoom.disable()
    const el = map.getContainer()
    let acc = 0
    const onWheel = (e: WheelEvent) => {
      if (!e.ctrlKey && !e.metaKey) return
      e.preventDefault()
      acc += e.deltaY
      if (Math.abs(acc) < 40) return
      const step = acc < 0 ? 1 : -1
      acc = 0
      map.setZoomAround(map.mouseEventToContainerPoint(e as unknown as MouseEvent), map.getZoom() + step)
    }
    el.addEventListener("wheel", onWheel, { passive: false })
    return () => el.removeEventListener("wheel", onWheel)
  }, [map])
  return null
}

/** Frame for a map. */
export function MapShell({ className, children }: { className?: string; children: ReactNode }) {
  return <div className={cn("relative overflow-hidden rounded-2xl bg-[#1c1c1e]", className)}>{children}</div>
}

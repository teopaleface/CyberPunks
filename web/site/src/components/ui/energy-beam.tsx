import React, { useEffect, useRef } from "react"

interface EnergyBeamProps {
  projectId?: string
  className?: string
}

declare global {
  interface Window {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    UnicornStudio?: any
  }
}

const SCRIPT_SRC =
  "https://cdn.jsdelivr.net/gh/hiunicornstudio/unicornstudio.js@v1.5.2/dist/unicornStudio.umd.js"

/**
 * Energy beam background (Unicorn Studio scene), from
 * 21st.dev/@sensewood8/components/energy-beam.
 * Change from the original: the script tag is shared, so a remount
 * (React StrictMode, route change) re-inits instead of loading it twice.
 */
const EnergyBeam: React.FC<EnergyBeamProps> = ({
  projectId = "hRFfUymDGOHwtFe7evR2",
  className = "",
}) => {
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const init = () => {
      if (window.UnicornStudio && containerRef.current) {
        window.UnicornStudio.init()
      }
    }

    const existing = document.querySelector<HTMLScriptElement>(
      `script[src="${SCRIPT_SRC}"]`
    )
    if (existing) {
      if (window.UnicornStudio) init()
      else existing.addEventListener("load", init, { once: true })
      return
    }

    const script = document.createElement("script")
    script.src = SCRIPT_SRC
    script.async = true
    script.onload = init
    document.head.appendChild(script)
  }, [projectId])

  return (
    <div className={`relative w-full h-screen bg-black overflow-hidden ${className}`}>
      <div ref={containerRef} data-us-project={projectId} className="w-full h-full" />
    </div>
  )
}

export default EnergyBeam

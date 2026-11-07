import { cva, type VariantProps } from "class-variance-authority"
import { forwardRef, type AnchorHTMLAttributes, type ButtonHTMLAttributes, type ReactNode } from "react"
import { cn } from "@/lib/utils"

/**
 * Liquid-glass CTA in the page's yellow and white.
 * Layers: tinted glass body (backdrop blur + saturate), a bright rim,
 * a specular highlight on the top edge, and a warm inner glow that
 * rises on hover. A light sweep crosses the glass on hover.
 */
const glass = cva(
  [
    "group/glass relative isolate inline-flex items-center justify-center gap-2 overflow-hidden",
    "rounded-full font-medium tracking-[-0.01em] whitespace-nowrap select-none cursor-pointer",
    "backdrop-blur-xl backdrop-saturate-150",
    "transition-[transform,box-shadow,background-color] duration-300 ease-[var(--ease-out)]",
    "hover:-translate-y-0.5 active:translate-y-0 active:scale-[0.97]",
    "focus-visible:outline-2 focus-visible:outline-offset-4",
    // specular rim + top highlight
    "before:pointer-events-none before:absolute before:inset-0 before:rounded-[inherit] before:p-px",
    "before:[background:linear-gradient(180deg,rgba(255,255,255,.75),rgba(255,255,255,.08)_40%,rgba(255,255,255,.04)_60%,rgba(255,255,255,.35))]",
    "before:[mask:linear-gradient(#000_0_0)_content-box_exclude,linear-gradient(#000_0_0)]",
    // light sweep
    "after:pointer-events-none after:absolute after:inset-y-0 after:-left-1/2 after:w-1/3 after:-skew-x-12",
    "after:bg-white/25 after:blur-md after:opacity-0 after:transition-[transform,opacity] after:duration-700",
    "hover:after:translate-x-[420%] hover:after:opacity-100",
  ],
  {
    variants: {
      variant: {
        signal: [
          "bg-ember text-black shadow-[inset_0_1px_0_rgba(255,255,255,.5),0_4px_20px_-10px_rgba(255,197,2,.4)]",
          "hover:bg-ember-soft",
        ],
        ember: [
          "text-white bg-[linear-gradient(135deg,rgba(255,197,2,0.34),rgba(255,92,255,0.18))]",
          "shadow-[inset_0_1px_0_rgba(255,255,255,.55),inset_0_-10px_24px_rgba(255,197,2,.35),0_8px_32px_-8px_rgba(255,197,2,.65)]",
          "hover:bg-[linear-gradient(135deg,rgba(255,197,2,0.48),rgba(255,92,255,0.3))] hover:shadow-[inset_0_1px_0_rgba(255,255,255,.7),inset_0_-12px_28px_rgba(255,92,255,.5),0_12px_44px_-6px_rgba(255,197,2,.9)]",
        ],
        // the account actions: solid blue glass (24,65,232)
        blue: [
          "text-white bg-[linear-gradient(180deg,rgba(24,65,232,0.85),rgba(24,65,232,0.62))]",
          "shadow-[inset_0_1px_0_rgba(255,255,255,.5),inset_0_-10px_24px_rgba(24,65,232,.45),0_8px_30px_-8px_rgba(24,65,232,.75)]",
          "hover:bg-[linear-gradient(180deg,rgba(40,82,245,0.95),rgba(24,65,232,0.75))] hover:shadow-[inset_0_1px_0_rgba(255,255,255,.65),inset_0_-12px_28px_rgba(60,100,255,.5),0_12px_40px_-6px_rgba(24,65,232,.9)]",
        ],
        frost: [
          "text-white bg-white/[0.08]",
          "shadow-[inset_0_1px_0_rgba(255,255,255,.45),inset_0_-8px_20px_rgba(255,255,255,.06),0_8px_28px_-10px_rgba(0,0,0,.8)]",
          "hover:bg-white/[0.14]",
        ],
      },
      size: {
        sm: "h-11 px-4 text-sm",
        md: "h-12 px-6 text-[15px]",
        lg: "h-14 px-8 text-base",
      },
    },
    defaultVariants: { variant: "ember", size: "md" },
  }
)

type GlassVariants = VariantProps<typeof glass>

function Inner({ children }: { children: ReactNode }) {
  return <span className="relative z-10 inline-flex items-center gap-2">{children}</span>
}

export const GlassButton = forwardRef<
  HTMLButtonElement,
  ButtonHTMLAttributes<HTMLButtonElement> & GlassVariants
>(({ className, variant, size, children, ...props }, ref) => (
  <button ref={ref} className={cn(glass({ variant, size }), className)} {...props}>
    <Inner>{children}</Inner>
  </button>
))
GlassButton.displayName = "GlassButton"

export const GlassLink = forwardRef<
  HTMLAnchorElement,
  AnchorHTMLAttributes<HTMLAnchorElement> & GlassVariants
>(({ className, variant, size, children, ...props }, ref) => (
  <a ref={ref} className={cn(glass({ variant, size }), className)} {...props}>
    <Inner>{children}</Inner>
  </a>
))
GlassLink.displayName = "GlassLink"

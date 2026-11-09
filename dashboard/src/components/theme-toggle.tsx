import { Moon, Sun } from "lucide-react"
import { useTheme } from "@/components/theme-provider"
import { cn } from "@/lib/utils"

const OPTIONS = [
  { value: "light", label: "Light theme", Icon: Sun },
  { value: "dark", label: "Dark theme", Icon: Moon },
] as const

function resolvedTheme(theme: string) {
  if (theme !== "system") {
    return theme
  }
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light"
}

export function ThemeToggle() {
  const { theme, setTheme } = useTheme()
  const active = resolvedTheme(theme)

  return (
    <div className="inline-flex items-center gap-1 rounded-lg border bg-muted/40 p-1">
      {OPTIONS.map(({ value, label, Icon }) => (
        <button
          key={value}
          type="button"
          aria-label={label}
          aria-pressed={active === value}
          onClick={() => setTheme(value)}
          className={cn(
            "flex size-8 items-center justify-center rounded-md text-muted-foreground transition-colors hover:text-foreground",
            active === value && "bg-background text-foreground shadow-sm"
          )}
        >
          <Icon className="size-4" />
        </button>
      ))}
    </div>
  )
}

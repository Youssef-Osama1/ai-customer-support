import { Badge } from "@/components/ui/badge"

type Variant = "default" | "secondary" | "destructive" | "outline"

const VARIANTS: Record<string, Variant> = {
  processed: "default",
  answered: "default",
  processing: "secondary",
  open: "secondary",
  skipped: "outline",
  escalated: "destructive",
  failed: "destructive",
}

export function StatusBadge({ status }: { status: string }) {
  return <Badge variant={VARIANTS[status] ?? "outline"}>{status}</Badge>
}

/** Navigarea este în meniul lateral. Antetul păstrează numele consolei și căutarea. */
export function TopTabs() {
  return (
    <div className="flex min-w-0 flex-1 items-center gap-4 max-md:hidden">
      <span className="text-[14px] text-muted-foreground">Consola dispecerului</span>
    </div>
  );
}

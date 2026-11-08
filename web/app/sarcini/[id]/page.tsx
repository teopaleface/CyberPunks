import { ScopedPage, type ScopedSearchParams } from "@/components/operations/scoped-page";
export default function Page({ searchParams, params }: { searchParams: ScopedSearchParams; params: Promise<{ id: string }> }) {
  return <ScopedPage section="work-detail" searchParams={searchParams} params={params} />;
}

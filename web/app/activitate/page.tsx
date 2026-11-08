import { ScopedPage, type ScopedSearchParams } from "@/components/operations/scoped-page";
export default function Page({ searchParams }: { searchParams: ScopedSearchParams }) {
  return <ScopedPage section="activity" searchParams={searchParams} />;
}

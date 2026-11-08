"use client";
import { useEffect, useRef, useState } from "react";
import Image from "next/image";
import { Camera, ImagePlus, Loader2, Trash2, ImageOff } from "lucide-react";
import { Dialog, DialogContent, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { rows, text, type Row } from "@/lib/operations/types";
import "./finding-photos.css";

const UUID = /^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$/i;
export const MAX_FINDING_PHOTOS = 6;
export interface FindingPhoto extends Row { photo_id: string; work_item_id?: string; width?: number; height?: number; status?: string }
export function findingPhotos(value: unknown): FindingPhoto[] {
  return rows(value).filter((item): item is FindingPhoto => UUID.test(text(item.photo_id)));
}
export function photoSource(id: string, scenario: string): string {
  return `/api/operations/photos/${encodeURIComponent(id)}?scenario=${encodeURIComponent(scenario)}`;
}
function PhotoImage({ photo, scenario, full = false, index }: { photo: FindingPhoto; scenario: string; full?: boolean; index: number }) {
  const [failed, setFailed] = useState(false);
  if (failed) return <span className="fp-unavailable"><ImageOff size={20} />Photo unavailable</span>;
  return full ? <Image unoptimized src={photoSource(photo.photo_id, scenario)} alt={`Finding photo ${index + 1}`} width={photo.width || 1024} height={photo.height || 768} onError={() => setFailed(true)} className="fp-full-image" />
    : <Image unoptimized fill sizes="(max-width:600px) 42vw, 180px" src={photoSource(photo.photo_id, scenario)} alt={`Finding photo ${index + 1}`} onError={() => setFailed(true)} className="fp-tile-image" />;
}
export function FindingPhotoGallery({ photos, scenario, onRemove, disabled = false }: { photos: FindingPhoto[]; scenario: string; onRemove?: (id: string) => void; disabled?: boolean }) {
  if (!photos.length) return null;
  return <div className="fp-gallery" aria-label="Finding photos">{photos.map((photo, index) => <div className="fp-photo" key={photo.photo_id}>
    <Dialog><DialogTrigger asChild><button type="button" className="fp-photo-open" aria-label={`Open finding photo ${index + 1}`}><PhotoImage photo={photo} index={index} scenario={scenario} /><span>Photo {index + 1}</span></button></DialogTrigger>
      <DialogContent className="fp-dialog sm:max-w-4xl"><DialogTitle>Finding photo {index + 1}</DialogTitle><PhotoImage photo={photo} index={index} scenario={scenario} full /></DialogContent></Dialog>
    {onRemove ? <button type="button" className="fp-remove" aria-label={`Remove photo ${index + 1} from this draft`} disabled={disabled} onClick={() => onRemove(photo.photo_id)}><Trash2 size={14} />Remove</button> : null}
  </div>)}</div>;
}
export function FindingPhotoInput({ workItemId, scenario, photoIds, initialPhotos, onChange, disabled, onBusy }: {
  workItemId: string; scenario: string; photoIds: string[]; initialPhotos: unknown; onChange: (ids: string[]) => void; disabled: boolean; onBusy?: (busy: boolean) => void;
}) {
  const [uploaded, setUploaded] = useState<FindingPhoto[]>([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const fileInput = useRef<HTMLInputElement>(null), cameraInput = useRef<HTMLInputElement>(null);
  const controller = useRef<AbortController | null>(null);
  const active = useRef(true);
  const uploadedIds = useRef(new Set<string>());
  useEffect(() => {
    active.current = true;
    const owned = uploadedIds.current;
    return () => {
      active.current = false; controller.current?.abort(); onBusy?.(false);
      // Bound proposals and saved evidence are protected by the server. Unused uploads can be removed.
      for (const id of owned) void fetch(photoSource(id, scenario), { method: "DELETE", credentials: "same-origin", keepalive: true }).catch(() => {});
    };
  }, [onBusy, scenario]);
  const combined = [...findingPhotos(initialPhotos), ...uploaded];
  const selected = photoIds.filter((id) => UUID.test(id)).map((id) => combined.find((photo) => photo.photo_id === id) ?? { photo_id: id });
  async function add(files: FileList | null) {
    if (!files?.length || busy || disabled || !workItemId) return;
    if (photoIds.length + files.length > MAX_FINDING_PHOTOS) { setError("You can attach up to 6 photos to one finding."); return; }
    const input = [...files];
    if (input.some((file) => !["image/jpeg", "image/png", "image/webp"].includes(file.type))) { setError("Choose JPG, PNG or WebP photos."); return; }
    if (input.some((file) => file.size > 5 * 1024 * 1024 || !file.size)) { setError("Each photo must be between 1 byte and 5 MB."); return; }
    setError(""); setBusy(true); onBusy?.(true);
    const abort = new AbortController(); controller.current = abort;
    const ids = [...photoIds];
    try {
      for (const file of input) {
        const response = await fetch(`/api/operations/work-items/${encodeURIComponent(workItemId)}/photos?scenario=${encodeURIComponent(scenario)}`, {
          method: "POST", credentials: "same-origin", headers: { "content-type": file.type }, body: file, signal: abort.signal,
        });
        const body = await response.json();
        if (!response.ok) throw new Error(body.error || "The photo could not upload. Try again.");
        const photo = findingPhotos([body])[0];
        if (!photo || photo.work_item_id !== workItemId) throw new Error("The photo was not accepted for this work item.");
        uploadedIds.current.add(photo.photo_id);
        if (!active.current) {
          void fetch(photoSource(photo.photo_id, scenario), { method: "DELETE", credentials: "same-origin", keepalive: true }).catch(() => {});
          return;
        }
        ids.push(photo.photo_id);
        setUploaded((previous) => [...previous, photo]);
        onChange([...ids]);
      }
    } catch (issue) {
      if (active.current && !(issue instanceof DOMException && issue.name === "AbortError")) setError(issue instanceof Error ? issue.message : "The photo could not upload.");
    } finally { if (active.current) { setBusy(false); onBusy?.(false); } }
  }
  function remove(id: string) {
    onChange(photoIds.filter((value) => value !== id));
    // A prepared proposal may still reference this photo. The server preserves its evidence.
    void fetch(photoSource(id, scenario), { method: "DELETE", credentials: "same-origin" }).catch(() => {});
  }
  const blocked = disabled || busy || !workItemId || photoIds.length >= MAX_FINDING_PHOTOS;
  return <section className="fp-input" aria-label="Add finding photos">
    <div className="fp-heading"><div><h4>Photos <span>Optional</span></h4><p>Show the asset, the issue or the access problem.</p></div><span className="fp-counter">{photoIds.length}/6</span></div>
    <FindingPhotoGallery photos={selected} scenario={scenario} onRemove={remove} disabled={disabled || busy} />
    <div className="fp-upload-actions"><button type="button" className="db-button" disabled={blocked} onClick={() => fileInput.current?.click()}>{busy ? <Loader2 size={16} className="animate-spin" /> : <ImagePlus size={16} />} {busy ? "Uploading…" : "Add photos"}</button><button type="button" className="db-button" disabled={blocked} onClick={() => cameraInput.current?.click()}><Camera size={16} />Take photo</button></div>
    <input ref={fileInput} aria-label="Choose finding photos" type="file" accept="image/jpeg,image/png,image/webp" multiple disabled={blocked} className="sr-only" onChange={(event) => { void add(event.target.files); event.target.value = ""; }} />
    <input ref={cameraInput} aria-label="Take a finding photo" type="file" accept="image/jpeg,image/png,image/webp" capture="environment" disabled={blocked} className="sr-only" onChange={(event) => { void add(event.target.files); event.target.value = ""; }} />
    <p className="fp-help">JPG, PNG or WebP · Up to 5 MB each. Photos attach to the finding only after Confirm.</p>
    {!workItemId ? <p className="fp-help">Choose the assigned work first.</p> : null}
    {error ? <p className="fp-error" role="alert">{error}</p> : null}
  </section>;
}

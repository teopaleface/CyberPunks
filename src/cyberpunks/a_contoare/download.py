"""Descărcarea datelor pentru firul A, cu sume de control (SHA-256).

    uv run python -m cyberpunks.a_contoare.download            # tot
    uv run python -m cyberpunks.a_contoare.download --only sgcc
    uv run python -m cyberpunks.a_contoare.download --only lcl

Datele brute stau în data/raw/A/ (în afara git). În git intră doar acest script și sumele de control.

Surse:
- SGCC (State Grid Corporation of China), publicat de Zheng et al. 2018 (IEEE TII, DOI 10.1109/TII.2017.2785963),
  https://github.com/henryRDlab/ElectricityTheftDetection . Repo-ul nu are licență explicită; cere citarea articolului.
  Folosim datele doar pentru cercetare, fără să le redistribuim.
- Low Carbon London (UK Power Networks), "SmartMeter Energy Consumption Data in London Households",
  https://data.london.gov.uk/dataset/smartmeter-energy-use-data-in-london-households (licența: vezi docs/data/A.md).
"""

from __future__ import annotations

import argparse
import hashlib
import struct
import sys
import zlib
from pathlib import Path

import httpx

from cyberpunks.common.paths import DATA_RAW

RAW_A = DATA_RAW / "A"
SGCC_DIR = RAW_A / "sgcc"
LCL_DIR = RAW_A / "lcl"

SGCC_BASE = "https://github.com/henryRDlab/ElectricityTheftDetection/raw/master/"
# Arhiva e împărțită în 3 volume (zip "spanned"). Sumele sunt cele verificate la prima descărcare (7 nov. 2026).
SGCC_PARTS = {
    "data.z01": "c324df53c88358a50aa23fd843b1e15af06e7a20b72d901a98d957c304a52b67",
    "data.z02": "34a30c8eea0fdfa77d58e15cd01c5593ea354ead4cc408a1b87364f6c46d4ed7",
    "data.zip": "1e06ad5f5e13f56f2a72bea304864d259e060d6ad95b3b030a4ad050d8df82d4",
}
SGCC_CSV_SHA256 = "99f8fd315626b1f729a9a03a97cb52ed097ab4d43e5771e21554c9e0c369b9b7"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch(url: str, dest: Path, expected_sha256: str | None = None, *, quiet: bool = False) -> Path:
    """Descarcă `url` în `dest` (dacă nu există deja cu suma corectă) și verifică suma de control."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and (expected_sha256 is None or sha256_file(dest) == expected_sha256):
        if not quiet:
            print(f"există deja: {dest.relative_to(DATA_RAW.parent.parent)}")
        return dest
    tmp = dest.with_suffix(dest.suffix + ".part")
    with httpx.stream("GET", url, follow_redirects=True, timeout=httpx.Timeout(60.0, read=300.0)) as resp:
        resp.raise_for_status()
        with open(tmp, "wb") as fh:
            fh.writelines(resp.iter_bytes(1 << 20))
    got = sha256_file(tmp)
    if expected_sha256 and got != expected_sha256:
        tmp.unlink(missing_ok=True)
        raise SystemExit(f"Suma de control greșită pentru {url}: {got} (așteptat {expected_sha256})")
    tmp.replace(dest)
    if not quiet:
        print(f"descărcat: {dest.relative_to(DATA_RAW.parent.parent)} ({dest.stat().st_size / 1e6:.1f} MB, sha256 {got[:12]}…)")
    return dest


def join_spanned_zip(parts: list[Path], out: Path) -> Path:
    """Extrage singurul fișier dintr-o arhivă zip împărțită în volume (.z01, .z02, .zip), fără unelte externe.

    `zip -s 0` de pe macOS strică arhiva SGCC (CRC greșit), iar `zip -FF` cere confirmare interactivă,
    așa că citim direct antetul local și decomprimăm fluxul deflate.
    """
    buf = b"".join(p.read_bytes() for p in parts)
    off = 4 if buf[:4] == b"PK\x07\x08" else 0  # semnătura de arhivă împărțită
    sig, _ver, _flag, method, _t, _d, _crc, _cs, _us, name_len, extra_len = struct.unpack("<IHHHHHIIIHH", buf[off : off + 30])
    if sig != 0x04034B50 or method != 8:
        raise SystemExit("Arhiva SGCC nu are formatul așteptat (antet local zip, deflate).")
    start = off + 30 + name_len + extra_len
    cd = buf.rfind(b"PK\x01\x02")  # directorul central are dimensiunile și CRC-ul corecte
    fields = struct.unpack("<IHHHHHHIIIHHHHHII", buf[cd : cd + 46])
    crc, csize, usize = fields[7], fields[8], fields[9]
    dec = zlib.decompressobj(-15)
    data = dec.decompress(buf[start : start + csize]) + dec.flush()
    if len(data) != usize or zlib.crc32(data) != crc:
        raise SystemExit("Decomprimarea SGCC a dat un fișier corupt (CRC sau mărime greșită).")
    out.write_bytes(data)
    return out


def download_sgcc(quiet: bool = False) -> Path:
    csv = SGCC_DIR / "data.csv"
    if csv.exists() and sha256_file(csv) == SGCC_CSV_SHA256:
        if not quiet:
            print(f"SGCC gata: {csv}")
        return csv
    parts = [fetch(SGCC_BASE + name, SGCC_DIR / name, sha, quiet=quiet) for name, sha in SGCC_PARTS.items()]
    join_spanned_zip(parts, csv)
    got = sha256_file(csv)
    if got != SGCC_CSV_SHA256:
        raise SystemExit(f"data.csv are altă sumă de control: {got}")
    if not quiet:
        print(f"SGCC gata: {csv} ({csv.stat().st_size / 1e6:.0f} MB)")
    return csv


# Low Carbon London: arhiva "Partitioned LCL Data" (168 de CSV-uri a câte 1 mil. de rânduri, CC BY 4.0).
# Serverul acceptă cereri pe intervale de octeți, așa că luăm doar fișierele de care avem nevoie, nu 796 MB.
# Fișierele 0-134 au gospodăriile cu tarif fix (Std), în ordinea ID-ului; 135-167 au tariful dinamic (ToU).
LCL_URL = (
    "https://data.london.gov.uk/download/vqm0d/04feba67-f1a3-4563-98d0-f3071e3d56d1/Partitioned%20LCL%20Data.zip"
)
LCL_MEMBER = "Small LCL Data/LCL-June2015v2_{k}.csv"
LCL_DEFAULT_FILES = range(45)  # ~1.500 de gospodării Std
LCL_CHECKSUMS = Path(__file__).resolve().parents[3] / "data" / "samples" / "A" / "checksums_lcl.sha256"


RETRYABLE = (200, 429, 500, 502, 503, 504)  # 200 = serverul a ignorat intervalul (se întâmplă sub încărcare)


def _range_get(client: httpx.Client, url: str, start: int | None, end: int, attempts: int = 10,
               sleep=None) -> bytes:
    """Octeții [start, end] (inclusiv) dintr-un fișier de pe server; start=None cere ultimii `end` octeți.

    La HTTP 429 (prea multe cereri), 5xx sau 200 (serverul a ignorat cererea pe interval și ar trimite toată
    arhiva de 796 MB) închide răspunsul fără să-l citească, așteaptă și reîncearcă. Văzut în reproducerea din
    clona curată (7 nov., 16:10): după 15 fișiere, serverul din Londra a răspuns cu 200 în loc de 206.
    """
    import time

    sleep = sleep or time.sleep
    spec = f"bytes=-{end}" if start is None else f"bytes={start}-{end}"
    last = None
    for attempt in range(attempts):
        try:
            with client.stream("GET", url, headers={"Range": spec}) as r:
                last = r.status_code
                if r.status_code == 206:
                    return r.read()
                retry_after = r.headers.get("retry-after", "")
        except httpx.TransportError:
            if attempt == attempts - 1:
                raise
            sleep(2 * (attempt + 1))
            continue
        if last in RETRYABLE and attempt < attempts - 1:
            sleep(float(retry_after) if retry_after.isdigit() else min(60.0, 3.0 * 2**attempt))
            continue
        break
    raise SystemExit(
        f"Serverul nu a respectat cererea pe interval (HTTP {last}) pentru {url}, după {attempts} încercări. "
        "Reîncearcă peste câteva minute: make a-data (fișierele deja descărcate și verificate se păstrează)."
    )


def _zip_directory(client: httpx.Client, url: str) -> dict[str, tuple[int, int, int, int]]:
    """Citește doar directorul central al unui zip de pe server: nume -> (offset antet, comprimat, necomprimat, crc)."""
    tail = _range_get(client, url, None, 65536)  # ultimii 64 KB: acolo sunt directorul și sfârșitul arhivei
    eocd = tail.rfind(b"PK\x05\x06")
    if eocd < 0:
        raise SystemExit("Nu găsesc sfârșitul directorului zip (EOCD).")
    cd_size, cd_off = struct.unpack("<II", tail[eocd + 12 : eocd + 20])
    cd = _range_get(client, url, cd_off, cd_off + cd_size - 1)
    entries: dict[str, tuple[int, int, int, int]] = {}
    pos = 0
    while pos + 46 <= len(cd) and cd[pos : pos + 4] == b"PK\x01\x02":
        f = struct.unpack("<IHHHHHHIIIHHHHHII", cd[pos : pos + 46])
        crc, csize, usize, nlen, xlen, clen, lho = f[7], f[8], f[9], f[10], f[11], f[12], f[16]
        name = cd[pos + 46 : pos + 46 + nlen].decode("utf-8", errors="replace")
        entries[name] = (lho, csize, usize, crc)
        pos += 46 + nlen + xlen + clen
    return entries


def _fetch_member(client: httpx.Client, url: str, entry: tuple[int, int, int, int]) -> bytes:
    lho, csize, usize, crc = entry
    head = _range_get(client, url, lho, lho + 29)
    _sig, _v, _fl, method, _t, _d, _c, _cs, _us, nlen, xlen = struct.unpack("<IHHHHHIIIHH", head)
    start = lho + 30 + nlen + xlen
    raw = _range_get(client, url, start, start + csize - 1)
    data = zlib.decompress(raw, -15) if method == 8 else raw
    if len(data) != usize or zlib.crc32(data) != crc:
        raise SystemExit("Fișier LCL corupt la descărcare (CRC sau mărime greșită).")
    return data


def _read_checksums() -> dict[str, str]:
    if not LCL_CHECKSUMS.exists():
        return {}
    out = {}
    for line in LCL_CHECKSUMS.read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.startswith("#"):
            sha, name = line.split(maxsplit=1)
            out[name.strip()] = sha
    return out


def download_lcl(files: range | list[int] = LCL_DEFAULT_FILES, quiet: bool = False, workers: int = 2) -> list[Path]:
    """Descarcă fișierele LCL alese (doar ele, prin cereri pe intervale) și verifică sumele de control."""
    from concurrent.futures import ThreadPoolExecutor

    LCL_DIR.mkdir(parents=True, exist_ok=True)
    known = _read_checksums()
    targets = [(k, LCL_DIR / f"LCL-June2015v2_{k}.csv") for k in files]
    # Un fișier existent e complet: se scrie întâi ca .part și se redenumește doar după verificarea CRC.
    # Dacă e în manifest, suma lui trebuie să se potrivească (verificarea de mai jos).
    todo = [(k, p) for k, p in targets if not p.exists()]
    if todo:
        with httpx.Client(follow_redirects=True, timeout=httpx.Timeout(60.0, read=300.0)) as client:
            directory = _zip_directory(client, LCL_URL)

            def one(item: tuple[int, Path]) -> Path:
                k, path = item
                data = _fetch_member(client, LCL_URL, directory[LCL_MEMBER.format(k=k)])
                tmp = path.with_suffix(".csv.part")
                tmp.write_bytes(data)
                tmp.replace(path)
                return path

            with ThreadPoolExecutor(max_workers=workers) as pool:
                futures = [pool.submit(one, item) for item in todo]
                errors = []
                for fut in futures:
                    try:
                        path = fut.result()
                    except (SystemExit, Exception) as exc:  # noqa: BLE001 (raportăm toate eșecurile la final)
                        errors.append(str(exc))
                        continue
                    if not quiet:
                        print(f"descărcat: {path.name} ({path.stat().st_size / 1e6:.1f} MB)")
            if errors:
                missing = [p.name for _k, p in targets if not p.exists()]
                raise SystemExit(f"Descărcarea LCL e incompletă: lipsesc {len(missing)} fișiere ({', '.join(missing)}). "
                                 f"Prima eroare: {errors[0]}")
    # sume de control: verificăm față de manifest; fișierele noi se adaugă în manifest (care intră în git)
    sums = {}
    for _k, path in targets:
        got = sha256_file(path)
        if path.name in known and known[path.name] != got:
            raise SystemExit(f"Suma de control diferă pentru {path.name}: {got} (în manifest: {known[path.name]})")
        sums[path.name] = got
    merged = {**known, **sums}
    LCL_CHECKSUMS.parent.mkdir(parents=True, exist_ok=True)
    header = "# SHA-256 pentru fișierele Low Carbon London (Partitioned LCL Data), verificate de download.py\n"
    LCL_CHECKSUMS.write_text(
        header + "".join(f"{sha}  {name}\n" for name, sha in sorted(merged.items(), key=lambda kv: _lcl_index(kv[0]))),
        encoding="utf-8",
    )
    if not quiet:
        print(f"LCL gata: {len(targets)} fișiere în {LCL_DIR}")
    return [p for _k, p in targets]


def _lcl_index(name: str) -> int:
    try:
        return int(name.rsplit("_", 1)[1].split(".")[0])
    except (IndexError, ValueError):
        return 10**6


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", choices=["sgcc", "lcl"], default=None)
    ap.add_argument("--lcl-files", type=int, default=len(LCL_DEFAULT_FILES), help="câte fișiere LCL (de la 0)")
    args = ap.parse_args(argv)
    if args.only in (None, "sgcc"):
        download_sgcc()
    if args.only in (None, "lcl"):
        download_lcl(range(args.lcl_files))
    return 0


if __name__ == "__main__":
    sys.exit(main())

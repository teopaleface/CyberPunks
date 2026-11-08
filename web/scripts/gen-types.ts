/**
 * Generează web/lib/contracts.ts din ../contracts/*.schema.json (sursa lor e
 * src/cyberpunks/common/contracts.py, prin `make schemas`).
 *
 * Rulează: cd web && bun run gen:types
 *
 * Toate schemele intră într-un singur pachet, ca tipurile comune (Source, de
 * exemplu) să fie declarate o singură dată. Rezultatul e determinist: aceleași
 * scheme dau exact același fișier.
 */
import { readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { compile, type JSONSchema } from "json-schema-to-typescript";

type Json = null | boolean | number | string | Json[] | { [key: string]: Json };
type JsonObject = { [key: string]: Json };

const WEB_ROOT = path.resolve(import.meta.dir, "..");
const CONTRACTS_DIR = path.resolve(WEB_ROOT, "..", "contracts");
const OUT_FILE = path.join(WEB_ROOT, "lib", "contracts.ts");

/** [fișierul de schemă, numele tipului rădăcină] */
const SCHEMAS = [
  ["work_item", "WorkItem"],
  ["plan", "Plan"],
  ["audit", "AuditRecord"],
  ["model_report", "ModelReport"],
  ["series", "Series"],
] as const;

const HEADER = [
  "// generat din contracts/*.schema.json — nu edita manual",
  "// Regenerează cu: cd web && bun run gen:types",
  "",
  "",
].join("\n");

function isObject(value: Json | undefined): value is JsonObject {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

/** JSON cu chei sortate, ca să comparăm definiții identice scrise în altă ordine. */
function stableStringify(value: Json): string {
  if (Array.isArray(value)) return `[${value.map(stableStringify).join(",")}]`;
  if (isObject(value)) {
    const keys = Object.keys(value).sort();
    return `{${keys.map((k) => `${JSON.stringify(k)}:${stableStringify(value[k])}`).join(",")}}`;
  }
  return JSON.stringify(value);
}

/**
 * Adaptează schema Pydantic (draft 2020-12) pentru json-schema-to-typescript:
 * - `$ref: #/$defs/X` devine `#/definitions/X`;
 * - `prefixItems` (tupluri) devine `items` sub formă de listă;
 * - titlurile de pe câmpuri dispar (altfel ar apărea tipuri ca `AuditId = string`);
 *   rămân doar pe rădăcini și pe definiții, unde dau numele tipurilor;
 * - dicționarele cu chei dintr-o listă fixă (`propertyNames.enum`, de exemplu
 *   `sources_status` cu cheile A, B, C) devin obiecte cu acele chei, opționale.
 */
function normalize(node: Json, keepTitle: boolean): Json {
  if (Array.isArray(node)) return node.map((child) => normalize(child, false));
  if (!isObject(node)) return node;

  const propertyNames = node.propertyNames;
  if (isObject(propertyNames) && Array.isArray(propertyNames.enum) && isObject(node.additionalProperties)) {
    const valueSchema = normalize(node.additionalProperties, false);
    const rest: JsonObject = { ...node };
    delete rest.propertyNames;
    delete rest.additionalProperties;
    const keys = propertyNames.enum.filter((k): k is string => typeof k === "string");
    return normalize(
      {
        ...rest,
        properties: Object.fromEntries(keys.map((k) => [k, valueSchema])),
        additionalProperties: false,
      },
      keepTitle,
    );
  }

  const out: JsonObject = {};
  for (const [key, value] of Object.entries(node)) {
    if (key === "title" && !keepTitle) continue;
    if (key === "$defs") continue; // mutate separat în `definitions`
    if (key === "$ref" && typeof value === "string") {
      out[key] = value.replace(/^#\/\$defs\//, "#/definitions/");
      continue;
    }
    if (key === "prefixItems" && Array.isArray(value)) {
      out.items = value.map((child) => normalize(child, false));
      out.additionalItems = false;
      continue;
    }
    if (key === "properties" && isObject(value)) {
      const props: JsonObject = {};
      for (const [name, schema] of Object.entries(value)) props[name] = normalize(schema, false);
      out[key] = props;
      continue;
    }
    out[key] = normalize(value, false);
  }
  return out;
}

/** Scoate comentariile automate "This interface was referenced by…", care nu spun nimic util. */
function tidy(source: string): string {
  const kept = source
    .split("\n")
    .filter(
      (line) =>
        !/^\s*\* This interface was referenced by `Contracts`'s JSON-Schema$/.test(line) &&
        !/^\s*\* via the `definition` "[^"]+"\.$/.test(line),
    )
    .join("\n");
  return kept.replace(/^\s*\/\*\*\n\s*\*\/\n/gm, "").replace(/\n(\s*)\*\n(\s*)\*\//g, "\n$2*/");
}

async function main() {
  const definitions = new Map<string, Json>();
  const origin = new Map<string, string>();

  const addDefinition = (name: string, schema: Json, file: string) => {
    const existing = definitions.get(name);
    if (existing !== undefined && stableStringify(existing) !== stableStringify(schema)) {
      throw new Error(
        `Definiția "${name}" diferă între ${origin.get(name)} și ${file}. Verifică schemele din contracts/.`,
      );
    }
    definitions.set(name, schema);
    origin.set(name, file);
  };

  for (const [file, rootName] of SCHEMAS) {
    const fileName = `${file}.schema.json`;
    const raw = JSON.parse(await readFile(path.join(CONTRACTS_DIR, fileName), "utf8")) as Json;
    if (!isObject(raw)) throw new Error(`${fileName} nu conține un obiect JSON`);
    if (raw.title !== rootName) {
      throw new Error(`${fileName}: mă așteptam la title "${rootName}", am găsit "${String(raw.title)}"`);
    }
    const defs = isObject(raw.$defs) ? raw.$defs : {};
    for (const [name, schema] of Object.entries(defs)) addDefinition(name, normalize(schema, true), fileName);
    addDefinition(rootName, normalize(raw, true), fileName);
  }

  const sortedDefinitions: JsonObject = {};
  for (const name of [...definitions.keys()].sort()) sortedDefinitions[name] = definitions.get(name)!;

  const bundle: JsonObject = {
    title: "Contracts",
    description: "Toate contractele, după numele fișierului de schemă din contracts/.",
    type: "object",
    additionalProperties: false,
    required: SCHEMAS.map(([file]) => file),
    properties: Object.fromEntries(
      SCHEMAS.map(([file, rootName]) => [file, { $ref: `#/definitions/${rootName}` }]),
    ),
    definitions: sortedDefinitions,
  };

  const body = await compile(bundle as unknown as JSONSchema, "Contracts", {
    bannerComment: "",
    additionalProperties: false,
    declareExternallyReferenced: true,
    unreachableDefinitions: true,
    unknownAny: true,
    strictIndexSignatures: false,
    ignoreMinAndMaxItems: true,
    format: true,
    style: { printWidth: 100, semi: true, singleQuote: false, trailingComma: "all" },
    cwd: CONTRACTS_DIR,
  });

  await writeFile(OUT_FILE, HEADER + tidy(body).trimEnd() + "\n", "utf8");
  console.log(`scris ${path.relative(WEB_ROOT, OUT_FILE)} (${definitions.size} tipuri)`);
}

await main();

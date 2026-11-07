import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  // Override default ignores of eslint-config-next.
  globalIgnores([
    // Default ignores of eslint-config-next:
    ".next/**",
    "out/**",
    "build/**",
    "next-env.d.ts",
    // generate sau statice, nu cod de-al nostru
    "public/maplibre/**",
    "design/**",
    // site-ul de prezentare (Vite, separat), cu lintul lui
    "site/**",
  ]),
]);

export default eslintConfig;

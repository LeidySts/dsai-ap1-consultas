/// <reference types="vitest" />
import { fileURLToPath } from "node:url";
import react from "@vitejs/plugin-react";
import { defineConfig, normalizePath, type Plugin } from "vite";

const raiz = normalizePath(fileURLToPath(new URL(".", import.meta.url)));
const testes = normalizePath(fileURLToPath(new URL("../../tests/frontend", import.meta.url)));

/** Os testes ficam em tests/frontend (fora deste pacote): pacotes importados
 * por eles são resolvidos como se fossem importados daqui. */
function resolverPacotesDosTestes(): Plugin {
  return {
    name: "resolver-pacotes-dos-testes",
    enforce: "pre",
    resolveId(id, importer, opcoes) {
      if (!importer || !normalizePath(importer).startsWith(testes)) return null;
      if (id.startsWith(".") || id.startsWith("/") || id.startsWith("@/") || /^[A-Za-z]:/.test(id)) return null;
      return this.resolve(id, `${raiz}src/main.tsx`, { ...opcoes, skipSelf: true });
    },
  };
}

export default defineConfig({
  plugins: [react(), resolverPacotesDosTestes()],
  resolve: { alias: { "@": `${raiz}src` } },
  server: {
    proxy: { "/api": "http://localhost:8000" },
    fs: { allow: [raiz, testes] },
  },
  test: {
    dir: testes,
    include: ["**/*.test.{ts,tsx}"],
    environment: "jsdom",
    globals: true,
    setupFiles: [`${testes}/setup.ts`],
  },
});

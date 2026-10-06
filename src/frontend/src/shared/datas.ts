const FUSO = "America/Sao_Paulo";

/** Índice 0 = segunda ... 6 = domingo (igual ao backend). */
export const DIAS = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"];

export function formatarDataHora(iso: string): string {
  return new Intl.DateTimeFormat("pt-BR", { timeZone: FUSO, dateStyle: "short", timeStyle: "short" }).format(new Date(iso));
}

export function formatarData(iso: string): string {
  return new Intl.DateTimeFormat("pt-BR", { timeZone: FUSO, weekday: "short", day: "2-digit", month: "2-digit" }).format(
    new Date(iso),
  );
}

export function formatarHora(iso: string): string {
  return new Intl.DateTimeFormat("pt-BR", { timeZone: FUSO, hour: "2-digit", minute: "2-digit" }).format(new Date(iso));
}

/** Dia AAAA-MM-DD no fuso de São Paulo (para agrupar horários). */
export function diaLocal(iso: string): string {
  return new Intl.DateTimeFormat("en-CA", { timeZone: FUSO }).format(new Date(iso));
}

/** Soma dias a uma data AAAA-MM-DD. */
export function somarDias(dia: string, dias: number): string {
  const d = new Date(`${dia}T12:00:00Z`);
  d.setUTCDate(d.getUTCDate() + dias);
  return d.toISOString().slice(0, 10);
}

/** Segunda-feira da semana de uma data AAAA-MM-DD. */
export function inicioDaSemana(dia: string): string {
  const semana = new Date(`${dia}T12:00:00Z`).getUTCDay(); // 0 = domingo
  return somarDias(dia, -((semana + 6) % 7));
}

/** Valor de <input type="datetime-local"> no horário de São Paulo (UTC-3, sem horário de verão) -> ISO. */
export function localParaIso(valor: string): string {
  return `${valor.length === 16 ? `${valor}:00` : valor}-03:00`;
}

export function formatarPreco(centavos: number): string {
  return (centavos / 100).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

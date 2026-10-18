export function parseXml(input: string): unknown {
  const parser = new DOMParser();
  return parser.parseFromString(input, "text/xml");
}

export async function fetchAvatar(url: string): Promise<void> {
  const resp = await fetch(url);
  await Object.assign({}, resp);
}

export async function loadRaw(db: unknown, q: string): Promise<unknown> {
  return await (db as { execute: (s: string) => Promise<unknown> }).execute(q);
}

class Auditor {
  audit(item: unknown): void {
    console.log(item);
  }
}

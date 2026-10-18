// 出处:人工构造(依据 CWE-611 xml2js parseStringPromise + import 形态)
import { parseStringPromise } from 'xml2js';
export async function ingestJob(xmlPayload: string) {
  const parsed = await parseStringPromise(xmlPayload, { trim: true });
  await queue.publish('jobs.parsed', parsed);
}

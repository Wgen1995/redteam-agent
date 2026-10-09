// tanyin-skills: 探隐技能 provider（superpowers-dsh 模式）。
// 把包内 skills/<name>/SKILL.md 注册进宿主 ctx.skills 注册表（HOST 层），
// 任何 agent preset 的 scope 链都会并入这些技能。协议镜像
// @deepseek-ai/dsh-skill-filesystem：list() 只发现（frontmatter 元数据，
// 正文按需）；get() 返回完整定义+directory resourceBase（相对引用可用）。
// @module tanyin-skills
import { readdir, readFile } from 'node:fs/promises'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'

const name = 'tanyin-skills'
const inject = ['skills']

/** 打包技能的注册表优先级：低于本地 bundled 根（与 superpowers-dsh 一致）。 */
const PACKAGED_SKILL_RANK = 550
/** 来源桶（prompt 可见元数据）。 */
const SOURCE = 'custom'

/** 解析 SKILL.md 的 YAML frontmatter（标量字段），正文原样返回。 */
function parseFrontmatter(text) {
  if (!text.startsWith('---')) return null
  const end = text.indexOf('\n---', 3)
  if (end === -1) return null
  const block = text.slice(3, end)
  const body = text.slice(end + 4).replace(/^\n+/, '')
  const metadata = {}
  for (const line of block.split('\n')) {
    const m = line.match(/^([A-Za-z_][\w-]*):\s*(.*)$/)
    if (m && m[2] !== undefined) metadata[m[1]] = m[2].replace(/^['"]|['"]$/g, '')
  }
  return { metadata, body }
}

/** 读取并解析一个技能目录的 SKILL.md。 */
async function parseSkillFile(skillFile) {
  let text
  try { text = await readFile(skillFile, 'utf8') } catch { return undefined }
  const parsed = parseFrontmatter(text)
  if (parsed === null) return undefined
  return {
    name: parsed.metadata.name ?? '',
    description: parsed.metadata.description ?? '',
    whenToUse: parsed.metadata.whenToUse,
    metadata: parsed.metadata,
    content: parsed.body,
  }
}

/** 扫描包内 skills/ 目录发现候选（一目录一技能）。 */
async function discoverCandidates(skillsRoot, signal) {
  let entries
  try { entries = await readdir(skillsRoot, { withFileTypes: true }) } catch { return [] }
  const candidates = []
  for (const entry of entries) {
    if (signal?.aborted) break
    if (!entry.isDirectory()) continue
    const skillDir = join(skillsRoot, entry.name)
    const parsed = await parseSkillFile(join(skillDir, 'SKILL.md'))
    if (parsed === undefined || !parsed.name) continue
    candidates.push({
      name: parsed.name,
      description: parsed.description,
      ...(parsed.whenToUse !== undefined ? { whenToUse: parsed.whenToUse } : {}),
      invocation: { modelInvocable: true, userInvocable: true },
      source: SOURCE,
      provider: name,
      rank: PACKAGED_SKILL_RANK,
      locator: skillDir,
      path: join(skillDir, 'SKILL.md'),
      ...(Object.keys(parsed.metadata).length > 0 ? { metadata: parsed.metadata } : {}),
    })
  }
  return candidates
}

/** 在 ctx.skills 注册打包技能 provider。 */
function apply(ctx) {
  const skillsRoot = join(dirname(fileURLToPath(import.meta.url)), '..', 'skills')
  ctx.skills.registerProvider((control) => ({
    name,
    async list(options) {
      return discoverCandidates(skillsRoot, options.signal)
    },
    async get(candidate, options) {
      const parsed = await parseSkillFile(candidate.path)
      if (parsed === undefined) return undefined
      if (options.signal?.aborted) return undefined
      return {
        name: parsed.name,
        description: parsed.description,
        ...(parsed.whenToUse !== undefined ? { whenToUse: parsed.whenToUse } : {}),
        invocation: { modelInvocable: true, userInvocable: true },
        source: SOURCE,
        provider: name,
        resourceBase: { kind: 'directory', path: candidate.locator },
        path: candidate.path,
        ...(Object.keys(parsed.metadata).length > 0 ? { metadata: parsed.metadata } : {}),
        content: parsed.content,
      }
    },
  }))
}

export { apply, name, inject }
export default { apply, name, inject }

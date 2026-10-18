// GT-ANCHOR-SNAPSHOT v1 — battlefield anchor carrier (excerpt only, not buildable)
// source-of-truth: ZhuLong repo (read-only) packages/contracts/src/domain/project.ts — regen: evals/gt/README.md §快照纪律
// ---- excerpt lines 8-20 ----
})
export type ProjectMemberCounts = z.infer<typeof ProjectMemberCountsSchema>

export const ProjectSchema = z.object({
  id: z.number().int(),
  name: z.string().min(1),
  domain: ProjectDomainSchema,
  ownerId: z.number().int(),
  sensitive: z.boolean(),                      // C-2 敏感开关（四眼项目级化·默认 false＝一人可全做；写权 admin only）
  deletedAt: z.number().int().nullable(),      // 软删（admin 恢复视图）
  createdAt: z.number().int(),
  updatedAt: z.number().int(),
  createdBy: z.number().int().nullable(),

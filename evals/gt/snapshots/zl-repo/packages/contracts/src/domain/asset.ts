// GT-ANCHOR-SNAPSHOT v1 — battlefield anchor carrier (excerpt only, not buildable)
// source-of-truth: ZhuLong repo (read-only) packages/contracts/src/domain/asset.ts — regen: evals/gt/README.md §快照纪律
// ---- excerpt lines 1-30 ----
import { z } from 'zod'
import {
  ObjectTypeSchema, ObjectSourceSchema, EnvKindSchema, VisibilitySchema,
  MachineTypeSchema, ResourcePoolSchema, ResourceStatusSchema,
} from '../enums'

export const TestObjectSchema = z.object({
  id: z.number().int(),
  name: z.string().min(1),
  objType: ObjectTypeSchema,
  source: ObjectSourceSchema,
  path: z.string().nullable().default(null),
  gitRef: z.string().nullable().default(null),
  sha256: z.string().nullable().default(null),
  ownerId: z.number().int(),
  visibility: VisibilitySchema.default('private'),
  deletedAt: z.number().int().nullable().default(null),
  createdAt: z.number().int(),
  updatedAt: z.number().int(),
  createdBy: z.number().int().nullable(),
})
export type TestObject = z.infer<typeof TestObjectSchema>

export const TestEnvironmentSchema = z.object({
  id: z.number().int(),
  name: z.string().min(1),
  envKind: EnvKindSchema,
  endpoint: z.string().nullable(),
  credref: z.string().nullable(),                                    // vault://env/<id>/<key>，明文永不回显
  fingerprint: z.record(z.string(), z.unknown()).nullable().default(null),

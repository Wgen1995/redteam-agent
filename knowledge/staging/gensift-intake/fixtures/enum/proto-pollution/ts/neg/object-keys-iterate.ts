// 出处:人工构造(硬负例:键枚举只读)
for (const key of Object.keys(payload)) {
  if (!ALLOWED.has(key)) throw new ValidationError(key);
}

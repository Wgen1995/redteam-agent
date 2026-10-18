// 出处:人工构造(依据 CWE-601 SPA 路由参数直推——次级向量)
export function useLoginRedirect() {
  const router = useRouter();
  return (to: string) => router.push(to);
}

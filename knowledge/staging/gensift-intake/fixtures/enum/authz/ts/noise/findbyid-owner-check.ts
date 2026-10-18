// 出处:人工构造(噪音:findById 后属主比对——sink 在,由五步判别,见 classes/fixture-spec.md §2)
export async function readDoc(docId: string, actor: string) {
  const doc = await DocModel.findById(docId).orFail();
  if (doc.owner !== actor) { throw new Error("not owner"); }
  return doc;
}

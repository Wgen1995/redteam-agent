# 出处:人工构造(硬负例:异步任务无文件面)
@shared_task
def reindex(doc_id: str):
    index.upsert(doc_id, fetcher(doc_id))

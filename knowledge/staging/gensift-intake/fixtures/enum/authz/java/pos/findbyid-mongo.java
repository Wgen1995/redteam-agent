// 出处:人工构造(依据 CWE-639 MongoTemplate 按 id 直查形态)
public Document download(String objectId) {
    Document doc = mongoTemplate.findById(objectId, Document.class);
    return doc;
}

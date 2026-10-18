// 出处:人工构造(硬负例:js-yaml 安全加载)
const cfg = YAML.load(fs.readFileSync(path, 'utf8'));

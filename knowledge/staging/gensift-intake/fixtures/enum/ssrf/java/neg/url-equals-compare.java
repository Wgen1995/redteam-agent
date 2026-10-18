// 出处:人工构造(硬负例:new URL 仅用于 equals 比较,不打外发)
URL candidate = new URL(submitted);
URL allowed = new URL("https://cdn.example.com");
if (!candidate.equals(allowed)) { throw new IllegalArgumentException("not allowed"); }

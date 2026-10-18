// 出处:人工构造(依据 CWE-918 Jsoup 抓取形态)
Document doc = Jsoup.connect(pageParam).timeout(5000).get();
Elements links = doc.select("a[href]");

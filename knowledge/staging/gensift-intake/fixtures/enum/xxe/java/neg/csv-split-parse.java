// 出处:人工构造(硬负例:CSV 解析)
for (String col : org.apache.commons.csv.CSVParser.parse(line, format)) { sink.accept(col); }

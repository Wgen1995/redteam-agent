// 出处:人工构造(硬负例:POI 导出——输出方向)
org.apache.poi.xssf.usermodel.XSSFWorkbook wb = new org.apache.poi.xssf.usermodel.XSSFWorkbook();
wb.write(resp.getOutputStream());

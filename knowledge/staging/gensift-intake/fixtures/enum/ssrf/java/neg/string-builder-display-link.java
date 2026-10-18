// 出处:人工构造(硬负例:拼 URL 仅用于页面展示)
StringBuilder link = new StringBuilder("https://profile.example.com/u/");
link.append(userName);
model.addAttribute("profileLink", link.toString());

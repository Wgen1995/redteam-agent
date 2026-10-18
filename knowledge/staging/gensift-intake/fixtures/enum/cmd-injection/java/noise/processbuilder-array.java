// 出处:人工构造(噪音:ProcessBuilder 数组形式安全用法——允许命中,由五步判别)
new ProcessBuilder("ffmpeg", "-i", inputFile, "-vn", outputAudio).start();

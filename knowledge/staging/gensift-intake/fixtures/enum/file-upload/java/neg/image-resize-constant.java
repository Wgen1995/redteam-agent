// 出处:人工构造(硬负例:固定输入图片处理)
java.awt.image.BufferedImage img = javax.imageio.ImageIO.read(new java.io.File("/opt/app/brand/logo.png"));
java.awt.image.BufferedImage thumb = img.getScaledInstance(64, 64, 4);

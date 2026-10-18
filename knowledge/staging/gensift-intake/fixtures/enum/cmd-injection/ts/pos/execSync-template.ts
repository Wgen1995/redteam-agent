// 出处:人工构造(ES 导入 + execSync 模板串)
import { execSync } from 'child_process';
execSync(`convert ${src} -resize 64x64 ${dst}`);

// 出处:人工构造(噪音:形态撞车登记——RxJS Observable.single 非 multer 中间件)
import { of } from 'rxjs';
const winner = of(...candidates).single();
winner.subscribe((v) => logger.debug('selected', v));

// 出处:人工构造(硬负例:Worker 线程非进程)
const w = new Worker('./worker.js', { workerData: payload });

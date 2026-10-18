// 出处:人工构造(依据 CWE-79 DOM 型:location.hash 进 innerHTML)
el.innerHTML = decodeURIComponent(location.hash.slice(1));

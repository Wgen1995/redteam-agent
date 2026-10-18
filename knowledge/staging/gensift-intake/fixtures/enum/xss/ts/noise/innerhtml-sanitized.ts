// 出处:人工构造(噪音:DOMPurify 净化后写入——允许命中)
el.innerHTML = DOMPurify.sanitize(userHtml);

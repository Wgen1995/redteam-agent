// 出处:人工构造(依据 CWE-79 React JSX 默认转义的例外 dangerouslySetInnerHTML)
const node = React.createElement("div", { dangerouslySetInnerHTML: { __html: userHtml } });

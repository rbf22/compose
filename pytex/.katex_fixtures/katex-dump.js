// Minimal KaTeX server-side renderer for generating HTML fixtures.
//
// Usage:
//   node katex-dump.js > fixtures.txt
//
// This prints named blocks of HTML for a set of TeX expressions that
// correspond to the fixtures in pytex/tests/test_katex_compat_html.py.

const katex = require("katex");

const fixtures = [
  {
    name: "inline_simple",
    tex: "x + y",
    options: { displayMode: false },
  },
  {
    name: "display_integral",
    tex: "\\int_{0}^{1} x^2 \\, dx",
    options: { displayMode: true },
  },
  {
    name: "fraction",
    tex: "\\frac{a}{b}",
    options: { displayMode: false },
  },
];

for (const { name, tex, options } of fixtures) {
  const html = katex.renderToString(tex, {
    ...options,
    output: "htmlAndMathml", // matches PyTeX default
    strict: "warn",
  });

  console.log("===" + name + "===");
  console.log(html);
  console.log();
}

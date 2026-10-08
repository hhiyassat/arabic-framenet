// Parity test: the matcher inside examples/index.html must give the same targets as api/afn_api.py.
// Expected results come from the API itself (examples/parity_cases.json, written by scripts/24_build_example_html.py).
// Usage: node tests/parity_example_vs_api.js     → prints PARITY_CASES / PARITY_MISMATCH ; exit 1 on any mismatch
const fs = require("fs"), path = require("path"), vm = require("vm");
const root = path.resolve(__dirname, "..");
const html = fs.readFileSync(path.join(root, "examples/index.html"), "utf8");
const js = html.slice(html.lastIndexOf("<script>") + 8, html.lastIndexOf("</script>"));
const sandbox = {module: {exports: {}}, console};
vm.runInNewContext(js + "\n;module.exports.D = D;", sandbox);
const {analyze, D} = sandbox.module.exports;
const cases = JSON.parse(fs.readFileSync(path.join(root, "examples/parity_cases.json"), "utf8"));
let bad = 0;
for (const c of cases) {
  const got = analyze(c.text, c.mode).targets.map(t => [t.span[0], t.span[1], t.match.method, t.match.lemma_key, t.ids.map(i => D.lus[i][7])]);
  if (JSON.stringify(got) !== JSON.stringify(c.targets)) {
    if (bad < 5) console.log("MISMATCH", c.mode, c.text.slice(0, 60), "\n  api ", JSON.stringify(c.targets), "\n  page", JSON.stringify(got));
    bad++;
  }
}
const targets = cases.reduce((n, c) => n + c.targets.length, 0);
console.log(`PARITY_CASES = ${cases.length}\nPARITY_TARGETS = ${targets}\nPARITY_MISMATCH = ${bad}\nPARITY = ${bad ? "FAIL" : "PASS"}`);
process.exit(bad ? 1 : 0);

'use strict';
// Runtime-only adapter. The analyzer receives the original Flow source.
const fs = require('fs');
const path = require('path');
const parser = require(path.resolve(__dirname, '../../tools/temporal-contract-analyzer/node_modules/@babel/parser'));
const source = fs.readFileSync(process.argv[2], 'utf8');
const ast = parser.parse(source, {sourceType: 'module', plugins: ['flow']});
const ranges = [];
function visit(node) {
  if (!node || typeof node !== 'object') return;
  if (['TypeAlias', 'TypeParameterDeclaration', 'TypeAnnotation'].includes(node.type)) {
    const start = node.type === 'TypeAnnotation' && source[node.start - 1] === '?' ? node.start - 1 : node.start;
    ranges.push({start, end: node.end, kind: node.type});
    return;
  }
  for (const [key, value] of Object.entries(node)) {
    if (['loc', 'comments', 'leadingComments', 'trailingComments', 'innerComments'].includes(key)) continue;
    if (Array.isArray(value)) value.forEach(visit);
    else if (value && typeof value === 'object') visit(value);
  }
}
visit(ast);
const chars = source.split('');
for (const range of ranges) {
  for (let i = range.start; i < range.end; i++) {
    if (!['\r', '\n', '\u2028', '\u2029'].includes(chars[i])) chars[i] = ' ';
  }
}
const erased = chars.join('');
parser.parse(erased, {sourceType: 'module'});
process.stdout.write(JSON.stringify({source: erased, erased_ranges: ranges, adapter: 'type-only-flow-erasure-v1'}));

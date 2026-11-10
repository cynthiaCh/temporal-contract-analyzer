'use strict';
// Inspect supplied source text only; never import the subject module.
const {createRequire} = require('node:module');
const path = require('node:path');
const parserRequire = createRequire(path.join(__dirname, '../../temporal_contract_analyzer/javascript/package.json'));
const parser = parserRequire('@babel/parser');
const functionTypes = new Set(['FunctionExpression', 'FunctionDeclaration', 'ArrowFunctionExpression']);
const isFunction = node => functionTypes.has(node?.type);
const member = (node, object, property) => node?.type === 'MemberExpression' && !node.computed &&
  node.object.type === 'Identifier' && node.object.name === object && node.property.name === property;

function walk(node, visit, skipFunctions = false) {
  if (!node || typeof node !== 'object') return;
  if (Array.isArray(node)) { for (const child of node) walk(child, visit, skipFunctions); return; }
  if (skipFunctions && isFunction(node)) return;
  visit(node);
  for (const [key, value] of Object.entries(node)) {
    if (!['loc', 'extra', 'comments', 'leadingComments', 'trailingComments', 'innerComments'].includes(key))
      walk(value, visit, skipFunctions);
  }
}

function bindings(statements) {
  const found = new Map();
  for (const node of statements) {
    if (node.type === 'FunctionDeclaration') found.set(node.id.name, node);
    if (node.type === 'VariableDeclaration') for (const declaration of node.declarations)
      if (declaration.id.type === 'Identifier') found.set(declaration.id.name, declaration.init);
  }
  return found;
}

function discover(text) {
  let program;
  try { program = parser.parse(text, {sourceType: 'script'}).program; }
  catch (error) { return {status: 'unsupported', reason: 'parse_error', detail: error.message}; }
  const exports = program.body.filter(node => node.type === 'ExpressionStatement' &&
    node.expression.type === 'AssignmentExpression' && node.expression.operator === '=' &&
    member(node.expression.left, 'module', 'exports'));
  if (exports.length !== 1) return {status: 'unsupported', reason: 'requires_one_direct_commonjs_export'};
  let factory = exports[0].expression.right;
  const top = bindings(program.body);
  if (factory.type === 'Identifier') factory = top.get(factory.name);
  if (!isFunction(factory) || factory.async || factory.generator || factory.params.length !== 1 ||
      factory.params[0].type !== 'Identifier')
    return {status: 'unsupported', reason: 'requires_single_callback_factory'};
  const callback = factory.params[0].name;
  const local = bindings(factory.body.type === 'BlockStatement' ? factory.body.body : []);
  const returns = [];
  if (factory.body.type !== 'BlockStatement') returns.push(factory.body);
  else walk(factory.body, node => { if (node.type === 'ReturnStatement') returns.push(node.argument); }, true);
  const functions = returns.map(node => node?.type === 'Identifier' ? local.get(node.name) : node);
  if (!functions.length || functions.some(node => !isFunction(node) || node.async || node.generator))
    return {status: 'unsupported', reason: 'requires_local_returned_callable'};
  const calls = [];
  let shadowed = false;
  for (const fn of functions) walk(fn, node => {
    if (isFunction(node) && (node.id?.name === callback || node.params.some(param => param.name === callback))) shadowed = true;
    if (node.type === 'VariableDeclarator' && node.id.name === callback) shadowed = true;
    if (node.type === 'CallExpression' && ((node.callee.type === 'Identifier' && node.callee.name === callback) ||
        member(node.callee, callback, 'apply') || member(node.callee, callback, 'call'))) calls.push(node.loc.start.line);
  });
  if (shadowed || !calls.length) return {status: 'unsupported', reason: 'callback_alias_or_shadowing_unresolved'};
  return {status: 'candidate', api: {kind: 'wrapper'},
    evidence: {export_line: exports[0].loc.start.line, factory_line: factory.loc.start.line,
      callback_parameter: callback, callback_call_lines: [...new Set(calls)]},
    obligation_inferred: false};
}

let input = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', chunk => { input += chunk; });
process.stdin.on('end', () => {
  const request = JSON.parse(input);
  console.log(JSON.stringify(discover(request.source)));
});

'use strict';
// Separate opt-in projection: do not change the frozen scanner AST payload.
// Only parse supplied snapshot text. Never load candidate modules or configs.
const parser = require('@babel/parser');
const fs = require('fs');
const crypto = require('crypto');
const hash = path => crypto.createHash('sha256').update(fs.readFileSync(path)).digest('hex');
const skip = new Set(['loc','start','end','extra','comments','tokens','leadingComments','trailingComments','innerComments']);
const loc = n => ({start_line:n.loc.start.line, end_line:n.loc.end.line - (n.loc.end.column===0 && n.loc.end.line>n.loc.start.line ? 1 : 0)});
const fn = n => /^(FunctionDeclaration|FunctionExpression|ArrowFunctionExpression|ObjectMethod|ClassMethod|ClassPrivateMethod)$/.test(n.type);

function script(file, source, ext, rootName) {
  const plugins = [];
  if(['ts','tsx'].includes(ext)) plugins.push('typescript');
  if(['js','jsx','mjs','cjs','tsx'].includes(ext)) plugins.push('jsx');
  const ast = parser.parse(source, {sourceType:'unambiguous', plugins});
  const bound = new WeakSet(), refs = [], gaps = [], exports = {};
  const root = {parent:null, names:new Map(), function:true};
  function bind(scope, name, value) {
    // Duplicate declarations are ambiguous; never silently select one.
    scope.names.set(name, scope.names.has(name) ? {ambiguous:true} : value);
  }
  function pattern(n, scope, value) {
    if(!n) return;
    if(n.type==='Identifier') { bound.add(n); bind(scope,n.name,value); }
    else if(n.type==='RestElement') pattern(n.argument,scope,value);
    else if(n.type==='AssignmentPattern') pattern(n.left,scope,value);
    else if(n.type==='ObjectPattern') n.properties.forEach(p=>pattern(p.type==='RestElement'?p.argument:p.value,scope,value));
    else if(n.type==='ArrayPattern') n.elements.forEach(x=>pattern(x,scope,value));
    else if(n.type==='TSParameterProperty') pattern(n.parameter,scope,value);
  }
  function definition(n, name) { return {kind:'local-definition', symbol:name, ...loc(n)}; }
  function bindingNames(n) {
    if(!n)return [];
    if(n.type==='Identifier')return [n.name];
    if(n.type==='RestElement')return bindingNames(n.argument);
    if(n.type==='AssignmentPattern')return bindingNames(n.left);
    if(n.type==='ObjectPattern')return n.properties.flatMap(p=>bindingNames(p.type==='RestElement'?p.argument:p.value));
    if(n.type==='ArrayPattern')return n.elements.flatMap(bindingNames);
    return [];
  }
  function visit(n, scope, parent, key) {
    if(!n || typeof n.type!=='string') return;
    // Type-only identifiers do not request runtime context.
    if(['TSEnumDeclaration','TSModuleDeclaration','TSImportEqualsDeclaration','TSExportAssignment'].includes(n.type)) {
      if(n.id?.type==='Identifier') {bound.add(n.id);bind(scope,n.id.name,{kind:'unsupported-definition',reason:'typescript-runtime-declaration-not-modeled'});}
      gaps.push({...loc(n),reason:'typescript-runtime-declaration-not-modeled'});return;
    }
    if(n.type.startsWith('TS') && !['TSAsExpression','TSSatisfiesExpression','TSNonNullExpression','TSTypeAssertion','TSInstantiationExpression','TSParameterProperty'].includes(n.type)) return;
    if(n.type==='FunctionDeclaration' || n.type==='ClassDeclaration') {
      if(n.id) { bound.add(n.id); bind(scope,n.id.name,definition(n,n.id.name)); }
    }
    let current=scope;
    if(fn(n) || ['BlockStatement','CatchClause','ForStatement','ForInStatement','ForOfStatement','SwitchStatement','ClassDeclaration','ClassExpression','StaticBlock'].includes(n.type)) {
      // Body var bindings must not shadow references in parameter initializers.
      current={parent:scope,names:new Map(),function:fn(n)||n.type==='StaticBlock'||(n.type==='BlockStatement' && parent && fn(parent) && key==='body')};
      if(fn(n)) {
        if(n.type==='FunctionExpression' && n.id) { bound.add(n.id); bind(current,n.id.name,definition(n,n.id.name)); }
        n.params.forEach(p=>pattern(p,current,{kind:'parameter'}));
      }
      if(n.type==='CatchClause') pattern(n.param,current,{kind:'parameter'});
      if(n.type==='ClassExpression' && n.id) { bound.add(n.id); bind(current,n.id.name,definition(n,n.id.name)); }
    }
    if(n.type==='VariableDeclarator') {
      let owner=current;
      if(parent.kind==='var') while(owner.parent && !owner.function) owner=owner.parent;
      // A whole declaration line can carry destructured names; all remain candidates.
      const value=definition(parent, n.id.name || '<destructured>');
      pattern(n.id,owner,value);
    }
    if(n.type==='ImportDeclaration') {
      for(const s of n.specifiers) {
        bound.add(s.local);
        if(n.importKind==='type' || s.importKind==='type') continue;
        bind(current,s.local.name,{kind:'import-definition',module:n.source.value,
          symbol:s.type==='ImportSpecifier'?(s.imported.name || s.imported.value):s.type==='ImportDefaultSpecifier'?'default':'*',local_name:s.local.name});
      }
    }
    if(n.type==='CallExpression' && (n.callee.type==='Import' || n.callee.name==='require')) gaps.push({...loc(n),reason:'dynamic-or-commonjs-import'});
    if(n.type==='ImportExpression') gaps.push({...loc(n),reason:'dynamic-or-commonjs-import'});
    if(n.type.startsWith('JSX')) gaps.push({...loc(n),reason:'jsx-context-not-modeled'});
    if(n.type==='WithStatement' || n.type==='CallExpression' && n.callee.name==='eval') gaps.push({...loc(n),reason:'dynamic-scope-not-modeled'});
    for(const [k,v] of Object.entries(n)) {
      if(skip.has(k) || ['typeAnnotation','typeParameters','typeArguments','returnType','implements','superTypeParameters'].includes(k)) continue;
      // Computed method names are evaluated outside the method's parameter scope.
      const childScope=fn(n) && (k==='key' || k==='decorators')?scope:current;
      if(Array.isArray(v)) v.forEach(child=>visit(child,childScope,n,k));
      else if(v && typeof v==='object') visit(v,childScope,n,k);
    }
    if(n.type==='Identifier') refs.push({node:n,parent,key,scope:current});
  }
  visit(ast.program,root,null,'');
  for(const n of ast.program.body) {
    if(n.type==='ExportNamedDeclaration') {
      if(n.exportKind==='type') continue;
      if(n.source) {
        for(const s of n.specifiers) exports[s.exported.name || s.exported.value]={reason:'reexport-not-supported'};
      } else if(n.declaration) {
        const d=n.declaration;
        const names=d.type==='VariableDeclaration'?d.declarations.flatMap(item=>bindingNames(item.id)):bindingNames(d.id);
        for(const name of names) {
          const value=root.names.get(name);
          if(value?.kind==='local-definition')exports[name]=value;
        }
      } else for(const s of n.specifiers) {
        if(s.exportKind==='type') continue;
        const d=root.names.get(s.local.name || s.local.value);
        exports[s.exported.name || s.exported.value]=d && d.kind==='local-definition'?d:{reason:'export-binding-not-supported'};
      }
    } else if(n.type==='ExportDefaultDeclaration') {
      const d=n.declaration;
      exports.default=d.type==='Identifier'?(root.names.get(d.name) || {reason:'export-binding-not-supported'}):definition(n,'default');
    } else if(n.type==='ExportAllDeclaration') gaps.push({...loc(n),reason:'reexport-not-supported'});
  }
  const references=[];
  for(const {node:n,parent:p,key,scope} of refs) {
    if(bound.has(n) || !p) continue;
    if(['ImportSpecifier','ImportDefaultSpecifier','ImportNamespaceSpecifier','ExportSpecifier'].includes(p.type)) continue;
    if(['MemberExpression','OptionalMemberExpression'].includes(p.type) && key==='property' && !p.computed) continue;
    if(['ObjectProperty','ObjectMethod','ClassMethod','ClassProperty','ClassPrivateProperty','ClassPrivateMethod'].includes(p.type) && key==='key' && !p.computed) continue;
    if(['LabeledStatement','BreakStatement','ContinueStatement'].includes(p.type) && key==='label') continue;
    if(p.type==='MetaProperty' || p.type==='PrivateName') continue;
    let owner=scope;
    while(owner && !owner.names.has(n.name)) owner=owner.parent;
    const binding=owner?.names.get(n.name);
    if(binding?.kind==='local-definition' || binding?.kind==='import-definition') references.push({...loc(n),name:n.name,binding,
      usage:['CallExpression','OptionalCallExpression','NewExpression'].includes(p.type) && key==='callee'?'call':'reference'});
    else if(binding?.kind==='unsupported-definition') gaps.push({...loc(n),symbol:n.name,reason:binding.reason});
    else if(binding?.ambiguous) gaps.push({...loc(n),symbol:n.name,reason:'ambiguous-binding'});
  }
  return {root:rootName,exports,references,gaps};
}

function analyze(file) {
  const ext=file.path.split('.').pop().toLowerCase();
  try {
    if(ext==='vue') {
      const {descriptor,errors}=require('@vue/compiler-sfc').parse(file.text,{filename:file.path,ignoreEmpty:false});
      if(errors.length) throw errors[0];
      if(descriptor.customBlocks.length || descriptor.template?.src) throw new Error('Unsupported external template or custom block');
      const blocks=[descriptor.script,descriptor.scriptSetup].filter(Boolean);
      const contexts=blocks.map(b=>{
        if(b.src || !['js','jsx','ts','tsx'].includes(b.lang || 'js')) throw new Error('Unsupported script block');
        const mask=s=>s.replace(/[^\r\n\u2028\u2029]/g,' ');
        const start=b.loc.start.offset,end=b.loc.end.offset;
        return script(file,mask(file.text.slice(0,start))+file.text.slice(start,end)+mask(file.text.slice(end)),b.lang||'js',b===descriptor.scriptSetup?'setup':'module');
      });
      return {path:file.path,status:'parsed',exports:descriptor.script?contexts[0].exports:{},
        references:contexts.flatMap(c=>c.references),gaps:[...contexts.flatMap(c=>c.gaps),{start_line:1,end_line:file.text.split('\n').length,reason:'vue-template-and-cross-block-bindings-not-modeled'}]};
    }
    if(!['js','jsx','mjs','cjs','ts','tsx'].includes(ext)) return {path:file.path,status:'unsupported-language',exports:{},references:[],gaps:[]};
    return {path:file.path,status:'parsed',...script(file,file.text,ext,'module')};
  } catch(e) {return {path:file.path,status:'parse-error',error:String(e.message||e),exports:{},references:[],gaps:[]};}
}
let input='';
process.stdin.setEncoding('utf8');
process.stdin.on('data',chunk=>input+=chunk);
process.stdin.on('end',()=>{
  try {
    const data=JSON.parse(input);
    process.stdout.write(JSON.stringify({parser:'@babel/parser',version:require('@babel/parser/package.json').version,
      library_sha256:hash(require.resolve('@babel/parser')),node:process.version,
      ...(data.files.some(f=>f.path.endsWith('.vue'))?{vue_version:require('@vue/compiler-sfc/package.json').version}:{}),
      files:data.files.map(analyze)}));
  } catch(e) {process.stderr.write(String(e.message)+'\n');process.exitCode=2;}
});

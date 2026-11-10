'use strict';
// Parse strings supplied on stdin; do not resolve, import or execute candidate modules.
const parser = require('@babel/parser');
const version = require('@babel/parser/package.json').version;
const fs = require('fs');
const library_sha256=require('crypto').createHash('sha256').update(fs.readFileSync(require.resolve('@babel/parser'))).digest('hex');
// Load the SFC parser only for Vue inputs; a missing Vue dependency must not
// prevent independent JavaScript files from being analyzed.
let sfc, sfcMetadata;
function analyzeVue(file) {
  const empty = {path:file.path,language:'vue',column_unit:'utf16_code_units',functions:[],events:[],imports:[],exports:{},bindings:[],
    analysis_scope:'inline script blocks only; template expressions, generated code and Vue runtime behavior are not analyzed'};
  if(!sfc) {
    try {
      const compiler = require('@vue/compiler-sfc');
      sfcMetadata = {parser:'@vue/compiler-sfc',version:require('@vue/compiler-sfc/package.json').version,
        library_sha256:require('crypto').createHash('sha256').update(fs.readFileSync(require.resolve('@vue/compiler-sfc/dist/compiler-sfc.cjs.js'))).digest('hex')};
      sfc = compiler;
    } catch(e) {
      return {...empty,status:'parser_unavailable',error:{message:'Vue parser unavailable; run npm ci --prefix temporal_contract_analyzer/javascript',line:null}};
    }
  }
  try {
    const {descriptor,errors} = sfc.parse(file.text,{filename:file.path,ignoreEmpty:false});
    if(errors.length) throw errors[0];
    if(descriptor.customBlocks.length) throw new Error('Vue custom blocks are not supported by this source scanner');
    if(descriptor.template?.src) throw new Error('External Vue templates are not supported by this source scanner');
    const blocks=[descriptor.script,descriptor.scriptSetup].filter(Boolean);
    const results=blocks.map(block=>{
      if(block.src) throw new Error('External <script src> is not supported; scan an inline script instead');
      const lang=block.lang || 'js';
      if(!['js','jsx','ts','tsx'].includes(lang)) throw new Error('Unsupported Vue script language: '+lang);
      // Adapted from temporal-contract-bench/tools/temporal-evidence/parse.cjs.
      // Preserve original UTF-16 offsets and line terminators. Do not compile
      // setup macros or templates, resolve imports, or execute candidate code.
      const start=block.loc.start.offset, end=block.loc.end.offset;
      const mask=s=>s.replace(/[^\r\n\u2028\u2029]/g,' ');
      const text=mask(file.text.slice(0,start))+file.text.slice(start,end)+mask(file.text.slice(end));
      return analyze({...file,text,scriptBlock:true,languageExt:lang,scopeName:block===descriptor.scriptSetup?'<setup>':'<module>'});
    });
    const failed=results.find(r=>r.status!=='parsed');
    if(failed) return {...empty,status:failed.status,error:failed.error};
    return {...empty,status:'parsed',functions:results.flatMap(r=>r.functions),
      events:results.flatMap((r,i)=>r.events.map(e=>({...e,id:(blocks[i]===descriptor.scriptSetup?'setup-':'script-')+e.id}))),
      imports:results.flatMap(r=>r.imports),bindings:results.flatMap(r=>r.bindings),
      // Only a normal script contributes module exports. Cross-block binding
      // and Vue component instance dispatch deliberately remain unresolved.
      exports:descriptor.script?results[0].exports:{}};
  } catch(e) {
    return {...empty,status:'parse_error',error:{message:String(e.message || e),line:e.loc?.start?.line || null}};
  }
}
function analyze(file) {
  if(file.path.toLowerCase().endsWith('.vue') && !file.scriptBlock) return analyzeVue(file);
  const source=file.text, functions=[],events=[],imports=[],exports={},bindings=[];
  const text=n=>n?source.slice(n.start,n.end):'';
  const name=n=>!n?'':n.type==='Identifier'?n.name:n.type==='ThisExpression'?'this':
    ['MemberExpression','OptionalMemberExpression'].includes(n.type)&&!n.computed?name(n.object)+'.'+name(n.property):'';
  const referenceName=n=>!n?'':n.type==='Identifier'?n.name:n.type==='ThisExpression'?'this':
    ['MemberExpression','OptionalMemberExpression'].includes(n.type)&&!n.computed&&referenceName(n.object)&&referenceName(n.property)?referenceName(n.object)+'.'+referenceName(n.property):'';
  const loc=n=>({line:n.loc.start.line,column:n.loc.start.column,end_line:n.loc.end.line,end_column:n.loc.end.column});
  const fnTypes=new Set(['FunctionDeclaration','FunctionExpression','ArrowFunctionExpression','ObjectMethod','ClassMethod','ClassPrivateMethod']);
  const callTypes=new Set(['CallExpression','OptionalCallExpression','NewExpression']);
  const syntaxKeys=new Set(['loc','extra','comments','leadingComments','trailingComments','innerComments','tokens','typeAnnotation','typeParameters','typeArguments','returnType','predicate','implements','superTypeParameters']);
  function earlyReturn(n){
    if(n?.type!=='IfStatement'||n.test.type!=='Identifier'||n.alternate)return false;
    const body=n.consequent.type==='BlockStatement'?n.consequent.body:[n.consequent];
    return body.length===1&&body[0].type==='ReturnStatement'&&
      (!body[0].argument||['Identifier','BooleanLiteral','NumericLiteral','StringLiteral','NullLiteral'].includes(body[0].argument.type));
  }
  function nullEarlyReturn(n){
    if(n?.type!=='IfStatement'||n.alternate||n.test.type!=='BinaryExpression'||n.test.operator!=='===')return '';
    const {left,right}=n.test;
    const identifier=left.type==='Identifier'&&right.type==='NullLiteral'?left.name:
      right.type==='Identifier'&&left.type==='NullLiteral'?right.name:'';
    const body=n.consequent.type==='BlockStatement'?n.consequent.body:[n.consequent];
    return identifier&&body.length===1&&body[0].type==='ReturnStatement'&&
      (!body[0].argument||['Identifier','BooleanLiteral','NumericLiteral','StringLiteral','NullLiteral'].includes(body[0].argument.type))?identifier:'';
  }
  function nullEarlyThrow(n){
    if(n?.type!=='IfStatement'||n.alternate||n.test.type!=='BinaryExpression'||n.test.operator!=='===')return '';
    const {left,right}=n.test;
    const identifier=left.type==='Identifier'&&right.type==='NullLiteral'?left.name:
      right.type==='Identifier'&&left.type==='NullLiteral'?right.name:'';
    const body=n.consequent.type==='BlockStatement'?n.consequent.body:[n.consequent];
    // No user code while constructing the exception: admit an identifier or
    // new Error with literal arguments, with lexical shadow checks downstream.
    const arg=body.length===1&&body[0].type==='ThrowStatement'?body[0].argument:null;
    return identifier&&(arg?.type==='Identifier'||arg?.type==='NewExpression'&&
      arg.callee.type==='Identifier'&&arg.callee.name==='Error'&&
      arg.arguments.every(a=>['StringLiteral','NumericLiteral','BooleanLiteral','NullLiteral'].includes(a.type)))?identifier:'';
  }
  function straightExpression(n){
    if(!n||typeof n!=='object')return true;
    if(fnTypes.has(n.type)||['AwaitExpression','YieldExpression','ConditionalExpression','LogicalExpression',
      'OptionalCallExpression','OptionalMemberExpression','ClassExpression','ClassDeclaration'].includes(n.type))return false;
    return Object.entries(n).every(([k,v])=>syntaxKeys.has(k)||
      (Array.isArray(v)?v.every(straightExpression):straightExpression(v)));
  }
  function linearStatement(n){
    return earlyReturn(n)||!!nullEarlyReturn(n)||!!nullEarlyThrow(n)||(['ExpressionStatement','VariableDeclaration','ReturnStatement','ThrowStatement','EmptyStatement'].includes(n.type)&&straightExpression(n));
  }
  function argumentCacheGuard(n){
    if(n?.type!=='IfStatement'||n.alternate)return null;
    const flatten=x=>x.type==='LogicalExpression'&&x.operator==='||'?[...flatten(x.left),...flatten(x.right)]:[x];
    const terms=flatten(n.test);
    if(terms.length!==3)return null;
    const missing=terms.find(x=>x.type==='UnaryExpression'&&x.operator==='!'&&x.argument.type==='Identifier');
    const receiver=terms.find(x=>x.type==='BinaryExpression'&&x.operator==='!=='&&x.left.type==='ThisExpression'&&x.right.type==='Identifier');
    const different=terms.find(x=>x.type==='UnaryExpression'&&x.operator==='!'&&x.argument.type==='CallExpression'&&
      x.argument.callee.type==='Identifier'&&x.argument.arguments.length===2&&x.argument.arguments.every(a=>a.type==='Identifier'));
    const body=n.consequent.type==='BlockStatement'?n.consequent.body:[n.consequent];
    if(!missing||!receiver||!different||different.argument.arguments[0].name!==missing.argument.name||
      !body.every(s=>s.type==='ExpressionStatement'&&s.expression.type==='AssignmentExpression'&&
        s.expression.operator==='='&&s.expression.left.type==='Identifier'&&straightExpression(s)))return null;
    return {key:missing.argument.name,receiver:receiver.right.name,arguments:different.argument.arguments[1].name,
      comparator:different.argument.callee.name};
  }
  function argumentCacheBody(n){
    return n.type==='BlockStatement'&&n.body.every(s=>!!argumentCacheGuard(s)||
      s.type==='VariableDeclaration'&&straightExpression(s)||
      s.type==='ReturnStatement'&&s.argument?.type==='Identifier');
  }
  // Source certificates for one small array-backed listener protocol. Compare
  // AST structure, not API names or whitespace. Unknown implementations stay unknown.
  function syntaxShape(n){
    if(Array.isArray(n))return n.map(syntaxShape);
    if(!n||typeof n!=='object')return n;
    return Object.fromEntries(Object.entries(n).filter(([k])=>!syntaxKeys.has(k)&&
      !['start','end'].includes(k)&&!(n.type==='VariableDeclaration'&&k==='kind')).map(([k,v])=>[k,syntaxShape(v)]));
  }
  function matchesBody(n,source){
    return JSON.stringify(syntaxShape(n.body))===JSON.stringify(syntaxShape(parser.parseExpression('function(){'+source+'}').body));
  }
  function listenerRemoval(n){
    if(n.params?.length!==2||!n.params.every(p=>p.type==='Identifier')||n.async||n.generator)return null;
    const body=n.body?.body;
    if(body?.length!==6||!body.slice(0,3).every(s=>s.type==='VariableDeclaration'&&s.declarations.length===1&&s.declarations[0].id.type==='Identifier'))return null;
    const [event,callback]=n.params.map(p=>p.name),[table,items,live]=body.slice(0,3).map(s=>s.declarations[0].id.name);
    const property=body[0].declarations[0].init?.left;
    if(property?.type!=='MemberExpression'||property.computed||property.object.type!=='ThisExpression'||property.property.type!=='Identifier')return null;
    const loop=body[3].type==='IfStatement'&&body[3].consequent.type==='BlockStatement'?body[3].consequent.body[0]:null;
    if(loop?.type!=='ForStatement'||loop.init?.type!=='VariableDeclaration'||loop.init.declarations.length!==2||
      !loop.init.declarations.every(d=>d.id.type==='Identifier'))return null;
    const [i,len]=loop.init.declarations.map(d=>d.id.name);
    const filter=loop.body?.body?.[0]?.test;
    const callbackProperty=filter?.left?.left?.property,aliasProperty=filter?.right?.left?.property;
    if(callbackProperty?.type!=='Identifier'||aliasProperty?.type!=='Identifier'||
      new Set([event,callback,table,items,live,i,len]).size!==7)return null;
    const p=property.property.name,f=callbackProperty.name,a=aliasProperty.name;
    const source=`var ${table}=this.${p}||(this.${p}={});var ${items}=${table}[${event}];var ${live}=[];
      if(${items}&&${callback}){for(var ${i}=0,${len}=${items}.length;${i}<${len};${i}++){
        if(${items}[${i}].${f}!==${callback}&&${items}[${i}].${f}.${a}!==${callback})${live}.push(${items}[${i}]);}}
      (${live}.length)?${table}[${event}]=${live}:delete ${table}[${event}];return this;`;
    return matchesBody(n,source)?{table_property:p,callback_property:f,alias_property:a}:null;
  }
  function listenerRegistration(n,removal){
    if(n.params?.length!==3||!n.params.every(p=>p.type==='Identifier')||n.async||n.generator)return false;
    const body=n.body?.body;
    if(body?.length!==3||body[0].type!=='VariableDeclaration'||body[0].declarations.length!==1||body[0].declarations[0].id.type!=='Identifier')return false;
    const [event,callback,context]=n.params.map(p=>p.name),table=body[0].declarations[0].id.name;
    const record=body[1].expression?.arguments?.[0];
    const contextProperty=record?.type==='ObjectExpression'&&record.properties.length===2?record.properties[1].key:null;
    if(contextProperty?.type!=='Identifier'||new Set([event,callback,context,table]).size!==4)return false;
    const p=removal.table_property,f=removal.callback_property,c=contextProperty.name;
    return matchesBody(n,`var ${table}=this.${p}||(this.${p}={});
      (${table}[${event}]||(${table}[${event}]=[])).push({${f}:${callback},${c}:${context}});return this;`);
  }
  function reflectiveStraight(n){
    if(!n||typeof n!=='object')return true;
    if(fnTypes.has(n.type)||['AwaitExpression','YieldExpression','LogicalExpression',
      'OptionalCallExpression','OptionalMemberExpression','ClassExpression','ClassDeclaration'].includes(n.type))return false;
    if(n.type==='ConditionalExpression'&&!(n.test.type==='BinaryExpression'&&n.test.operator==='instanceof'&&
      n.test.left.type==='ThisExpression'&&n.test.right.type==='Identifier'&&
      n.consequent.type==='CallExpression'&&n.alternate.type==='CallExpression'))return false;
    return Object.entries(n).every(([k,v])=>syntaxKeys.has(k)||
      (Array.isArray(v)?v.every(reflectiveStraight):reflectiveStraight(v)));
  }
  function objectBindings(n){
    if(n?.type!=='ObjectPattern'||!n.properties.every(p=>p.type==='ObjectProperty'&&!p.computed&&
      p.key.type==='Identifier'&&p.value.type==='Identifier'))return [];
    return n.properties.map(p=>({local:p.value.name,property:p.key.name}));
  }
  function countdownGuard(n){
    if(n?.type!=='IfStatement'||n.alternate||n.test.type!=='BinaryExpression'||n.test.operator!=='>')return null;
    const {left,right}=n.test;
    if(right.type!=='NumericLiteral'||!Number.isSafeInteger(right.value)||right.value<0)return null;
    let counter,form;
    if(left.type==='UpdateExpression'&&left.operator==='--'&&left.prefix&&left.argument.type==='Identifier'&&right.value<Number.MAX_SAFE_INTEGER){counter=left.argument.name;form='guard_prefix';}
    else if(left.type==='Identifier'){counter=left.name;form='plain';}
    else return null;
    const body=n.consequent.type==='BlockStatement'?n.consequent.body:[n.consequent];
    if(!body.every(s=>['ExpressionStatement','VariableDeclaration','EmptyStatement'].includes(s.type)&&straightExpression(s)))return null;
    return {counter,form,threshold:right.value};
  }
  function countdownCleanup(n){
    if(n?.type!=='IfStatement'||n.alternate||n.test.type!=='BinaryExpression'||n.test.operator!=='<='||
      n.test.left.type!=='Identifier'||n.test.right.type!=='NumericLiteral'||
      !Number.isSafeInteger(n.test.right.value)||n.test.right.value<0)return null;
    const body=n.consequent.type==='BlockStatement'?n.consequent.body:[n.consequent];
    const assignment=body.length===1&&body[0].type==='ExpressionStatement'?body[0].expression:null;
    if(assignment?.type!=='AssignmentExpression'||assignment.operator!=='='||assignment.left.type!=='Identifier'||assignment.right.type!=='NullLiteral')return null;
    return {counter:n.test.left.name,threshold:n.test.right.value,target:assignment.left.name};
  }
  function countdownBody(n){
    return n.type==='BlockStatement'&&n.body.every(s=>
      s.type==='EmptyStatement'||!!countdownGuard(s)||!!countdownCleanup(s)||
      s.type==='ReturnStatement'&&(!s.argument||['Identifier','BooleanLiteral','NumericLiteral','StringLiteral','NullLiteral'].includes(s.argument.type))||
      s.type==='VariableDeclaration'&&s.declarations.every(d=>d.id.type==='Identifier'&&(!d.init||['Identifier','BooleanLiteral','NumericLiteral','StringLiteral','NullLiteral'].includes(d.init.type)))||
      s.type==='ExpressionStatement'&&s.expression.type==='UpdateExpression'&&s.expression.operator==='--'&&s.expression.argument.type==='Identifier');
  }
  function supportedCondition(n,root=false){
    if(root&&references(n).length===0)return false;
    return ['Identifier','ThisExpression','BooleanLiteral','NumericLiteral','StringLiteral','NullLiteral'].includes(n.type)||
      (n.type==='UnaryExpression'&&n.operator==='!'&&supportedCondition(n.argument))||
      (n.type==='BinaryExpression'&&['===','!==','==','!='].includes(n.operator)&&supportedCondition(n.left)&&supportedCondition(n.right));
  }
  function boundNames(n){
    if(!n)return [];
    if(n.type==='Identifier')return [n.name];
    if(n.type==='AssignmentPattern')return boundNames(n.left);
    if(n.type==='RestElement')return boundNames(n.argument);
    if(n.type==='TSParameterProperty')return boundNames(n.parameter);
    if(n.type==='ObjectPattern')return n.properties.flatMap(p=>boundNames(p.type==='RestElement'?p.argument:p.value));
    if(n.type==='ArrayPattern')return n.elements.flatMap(boundNames);
    return [];
  }
  function writeRoots(n){
    if(n?.type==='ObjectPattern')return n.properties.flatMap(p=>writeRoots(p.type==='RestElement'?p.argument:p.value));
    if(n?.type==='ArrayPattern')return n.elements.flatMap(writeRoots);
    if(n?.type==='AssignmentPattern')return writeRoots(n.left);
    if(n?.type==='RestElement')return writeRoots(n.argument);
    while(n&&['MemberExpression','OptionalMemberExpression'].includes(n.type))n=n.object;
    return boundNames(n);
  }
  // Read only syntax, never identifier-looking strings, noncomputed keys, types,
  // or a function body's references when describing its enclosing expression.
  function references(n){
    const found=new Set();
    function visit(x){
      if(!x||typeof x.type!=='string'||fnTypes.has(x.type))return;
      if(x.type==='Identifier'||x.type==='ThisExpression'){found.add(name(x));return;}
      if(['MemberExpression','OptionalMemberExpression'].includes(x.type)){
        const dotted=referenceName(x);if(dotted){found.add(dotted);return;}
        visit(x.object);if(x.computed)visit(x.property);return;
      }
      if(['ObjectProperty','ObjectPattern'].includes(x.type)){
        if(x.type==='ObjectProperty'){if(x.computed)visit(x.key);visit(x.value);}
        else x.properties.forEach(visit);
        return;
      }
      if(x.type.startsWith('TS')&&!['TSAsExpression','TSSatisfiesExpression','TSNonNullExpression','TSTypeAssertion','TSInstantiationExpression'].includes(x.type))return;
      for(const [k,v] of Object.entries(x)){
        if(syntaxKeys.has(k))continue;
        if(Array.isArray(v))v.forEach(visit);else if(v&&typeof v==='object')visit(v);
      }
    }
    visit(n);return [...found];
  }
  const objectTargets=new WeakMap(), functionScopes=new WeakMap(),listenerMethods=new WeakMap();
  const counts={};
  function fn(n,parent,label){const key=parent+'/'+label;counts[key]=(counts[key]||0)+1;const id=key+(counts[key]>1?'#'+counts[key]:'');functions.push({id,parent,name:label,parameters:n.params.flatMap(boundNames),async:!!n.async,generator:!!n.generator,
    body_block:n.body.type==='BlockStatement'?id+'/block@'+n.body.start:id+'/body',
    countdown_body_supported:countdownBody(n.body),
    ...(argumentCacheBody(n.body)?{argument_cache_body_supported:true}:{}),
    ...(n.type==='FunctionExpression'&&n.id?{self_name:n.id.name}:{}),...loc(n)});return id;}
  const root=file.scopeName||'<module>';functions.push({id:root,parent:null,name:root,parameters:[],async:false,generator:false,body_block:root+'/block@0',line:1,column:0,end_line:source.split('\n').length,end_column:0});
  function emit(n,kind,ctx,extra={}){const e={id:'e'+events.length,kind,scope:ctx.scope,block:ctx.block,statement:ctx.statement,conditions:ctx.conditions,conditional_path:ctx.conditional_path||[],branch_path:ctx.branch_path||[],linear_block:!!ctx.linear_block,...(ctx.loop_bindings?.length?{loop_bindings:ctx.loop_bindings}:{}),...loc(n),text:text(n),...extra};events.push(e);return e;}
  function walk(n,ctx,parent=null,field='') {
    if(!n||typeof n.type!=='string')return;
    if(fnTypes.has(n.type)){
      let label=name(n.id)||name(n.key)||'';
      if(!label&&parent?.type==='VariableDeclarator')label=name(parent.id);
      if(!label&&parent?.type==='ObjectProperty')label=name(parent.key);
      if(!label)label='<callback>';
      const scope=fn(n,ctx.scope,label);
      functionScopes.set(n,scope);
      // Normally a header anchor. Certified listener methods retain their body
      // so reports can show the registration/removal implementation as evidence.
      const header=listenerMethods.has(n)?n:{...n,end:n.body.start,loc:{start:n.loc.start,end:n.body.loc.start}};
      const definition={...ctx,scope};delete definition.loop_bindings;
      emit(header,'function_definition',definition,{name:label,...(objectTargets.has(n)?{object_target:objectTargets.get(n)}:{}),
        ...(listenerMethods.has(n)?{listener_method:listenerMethods.get(n)}:{})});
      if(n.type==='FunctionDeclaration')bindings.push({scope:ctx.scope,block:ctx.block,name:label,target:scope});
      else if(parent?.type==='VariableDeclarator'&&parent.id.type==='Identifier')bindings.push({scope:ctx.scope,block:ctx.block,name:parent.id.name,target:scope});
      if(parent?.type==='ReturnStatement'||(parent?.type==='ArrowFunctionExpression'&&field==='body'))emit(header,'returned_callback',ctx,{target_scope:scope});
      if(callTypes.has(parent?.type)&&field==='arguments')emit(header,'callback_argument',ctx,{target_scope:scope,callee:name(parent.callee)||'<dynamic>',argument_index:parent.arguments.indexOf(n)});
      // Defaults execute when invoked; record as a conditional region, not the enclosing function.
      for(const p of n.params)if(p.type==='AssignmentPattern')walk(p.right,{scope,block:scope+'/defaults',statement:0,conditions:['parameter default is evaluated']},p,'right');
      walk(n.body,{scope,block:scope+'/body',statement:0,conditions:[]},n,'body');return;
    }
    if(n.type==='Program'||n.type==='BlockStatement'){
      const block=ctx.scope+'/block@'+n.start;
      const linear_block=n.body.every(linearStatement);
      n.body.forEach((s,i)=>walk(s,{...ctx,block,linear_block,statement:i},n,'body'));return;
    }
    if(n.type==='ClassDeclaration'||n.type==='ClassExpression'){
      if(n.type==='ClassDeclaration'&&n.id)emit(n.id,'binding',ctx,{declared_names:[n.id.name],binding_kind:'class'});
      // A lexical namespace only, not an instance dispatch/type model.
      walk(n.superClass,ctx,n,'superClass');
      for(const d of n.decorators||[])walk(d,ctx,n,'decorators');
      const label=name(n.id)||(parent?.type==='VariableDeclarator'?name(parent.id):'')||'<class>';
      const key=ctx.scope+'/'+label;counts[key]=(counts[key]||0)+1;
      const scope=key+(counts[key]>1?'#'+counts[key]:'');
      n.body.body.forEach((m,i)=>walk(m,{scope,block:scope+'/class-body',statement:i,conditions:[]},n.body,'body'));return;
    }
    if(n.type==='ImportDeclaration'){
      for(const spec of n.specifiers)imports.push({scope:ctx.scope,local:spec.local.name,module:n.source.value,symbol:spec.type==='ImportSpecifier'?name(spec.imported):spec.type==='ImportDefaultSpecifier'?'default':'*',...loc(n)});return;
    }
    if(n.type==='ExportNamedDeclaration'){
      if(n.declaration?.type==='FunctionDeclaration')exports[name(n.declaration.id)]=name(n.declaration.id);
      if(n.declaration?.type==='VariableDeclaration')for(const d of n.declaration.declarations)if(fnTypes.has(d.init?.type))exports[name(d.id)]=name(d.id);
      // Re-exports are deliberately unresolved.
    }
    if(n.type==='IfStatement'){
      const guard_key=ctx.scope+'/if@'+n.start;
      emit(n.test,'guard',ctx,{expression:text(n.test),references:references(n.test),guard_key,
        then_path_block:ctx.scope+(n.consequent.type==='BlockStatement'?'/block@'+n.consequent.start:'/then@'+n.start),
        else_path_block:ctx.scope+(n.alternate?.type==='BlockStatement'?'/block@'+n.alternate.start:'/else@'+n.start),
        condition_path_supported:supportedCondition(n.test,true),
        ...(n.test.type==='Identifier'?{condition_identifier:n.test.name,condition_truthy:true}:
          n.test.type==='UnaryExpression'&&n.test.operator==='!'&&n.test.argument.type==='Identifier'?
          {condition_identifier:n.test.argument.name,condition_truthy:false}:{}),
        ...(earlyReturn(n)?{early_return_identifier:n.test.name}:{}),
        ...(nullEarlyReturn(n)?{null_return_identifier:nullEarlyReturn(n)}:{}),
        ...(nullEarlyThrow(n)?{null_throw_identifier:nullEarlyThrow(n)}:{}),
        ...(argumentCacheGuard(n)?{argument_cache_guard:argumentCacheGuard(n)}:{}),
        ...(countdownGuard(n)?{countdown_guard:countdownGuard(n)}:{}),
        ...(countdownCleanup(n)?{countdown_cleanup:countdownCleanup(n)}:{}),
        ...(n.test.type==='Identifier'?{test_identifier:n.test.name,
          reflective_branch_linear:(n.consequent.type==='BlockStatement'?n.consequent.body:[n.consequent]).every(s=>
            ['ExpressionStatement','VariableDeclaration','ReturnStatement','ThrowStatement','EmptyStatement'].includes(s.type)&&reflectiveStraight(s)),
          consequent_block:ctx.scope+(n.consequent.type==='BlockStatement'?'/block@'+n.consequent.start:'/then@'+n.start),
          consequent_linear:(n.consequent.type==='BlockStatement'?n.consequent.body:[n.consequent]).every(s=>
            ['ExpressionStatement','VariableDeclaration','ReturnStatement','ThrowStatement','EmptyStatement'].includes(s.type))}: {})});walk(n.test,ctx,n,'test');
      walk(n.consequent,{...ctx,block:ctx.scope+'/then@'+n.start,branch_path:[...(ctx.branch_path||[]),{key:guard_key,arm:'then'}],conditions:[...ctx.conditions,'if '+text(n.test)]},n,'consequent');
      walk(n.alternate,{...ctx,block:ctx.scope+'/else@'+n.start,branch_path:[...(ctx.branch_path||[]),{key:guard_key,arm:'else'}],conditions:[...ctx.conditions,'else of '+text(n.test)]},n,'alternate');return;
    }
    if(n.type==='ConditionalExpression'||n.type==='LogicalExpression'){
      const cond=n.test||n.left;walk(cond,ctx,n,'test');
      const branch={...ctx,block:ctx.scope+'/conditional@'+n.start,conditions:[...ctx.conditions,'conditional expression '+text(cond)]};
      if(n.type==='ConditionalExpression'){
        const condition={key:branch.block,parent_block:ctx.block,expression:text(cond),
          operator:cond.operator||null,left:name(cond.left),right:name(cond.right)};
        walk(n.consequent,{...branch,conditional_path:[...(ctx.conditional_path||[]),{...condition,arm:'then'}]},n,'consequent');
        walk(n.alternate,{...branch,block:branch.block+'/else',conditional_path:[...(ctx.conditional_path||[]),{...condition,arm:'else'}]},n,'alternate');
      }
      else walk(n.right,branch,n,'right');return;
    }
    if(n.type==='TryStatement'){
      walk(n.block,ctx,n,'block');walk(n.handler,{...ctx,conditions:[...ctx.conditions,'catch path']},n,'handler');walk(n.finalizer,{...ctx,conditions:[...ctx.conditions,'finally path']},n,'finalizer');return;
    }
    if(n.type==='CatchClause'){
      if(n.param)emit(n.param,'binding',ctx,{declared_names:boundNames(n.param),binding_kind:'catch'});
      walk(n.param,ctx,n,'param');walk(n.body,ctx,n,'body');return;
    }
    if(['ForStatement','ForOfStatement','ForInStatement','WhileStatement','DoWhileStatement','SwitchStatement'].includes(n.type)){
      const c={...ctx,block:ctx.scope+'/control@'+n.start,conditions:[...ctx.conditions,n.type+' path; execution/repetition not proven']};
      let body=c;
      if(n.type==='ForOfStatement'){
        const target=n.left.type==='VariableDeclaration'?n.left.declarations[0].id:n.left;
        body={...c,loop_bindings:[...(ctx.loop_bindings||[]),{target:name(target)||text(target),iterable:text(n.right),iterable_references:references(n.right)}]};
      }
      for(const [k,v] of Object.entries(n))if(!syntaxKeys.has(k)){const region=k==='body'?body:c;if(Array.isArray(v))v.forEach(x=>walk(x,region,n,k));else if(v&&typeof v==='object')walk(v,region,n,k);}return;
    }
    if(n.type==='ObjectExpression'){
      const target=parent?.type==='VariableDeclarator'?referenceName(parent.id):parent?.type==='AssignmentExpression'?referenceName(parent.left):'';
      if(target)for(const p of n.properties){if(fnTypes.has(p.type))objectTargets.set(p,target);else if(p.type==='ObjectProperty'&&fnTypes.has(p.value?.type))objectTargets.set(p.value,target);}
      if(target&&n.properties.every(p=>!p.computed&&p.key?.type==='Identifier'&&p.key.name!=='__proto__'&&
        (p.type==='ObjectProperty'||p.type==='ObjectMethod'&&p.kind==='method'))){
        const methods=n.properties.filter(p=>!p.computed&&p.key?.type==='Identifier'&&
          (p.type==='ObjectMethod'||p.type==='ObjectProperty'&&fnTypes.has(p.value?.type)))
          .map(p=>({name:p.key.name,node:p.type==='ObjectMethod'?p:p.value}));
        for(const remove of methods){
          const certificate=listenerRemoval(remove.node);
          if(!certificate||n.properties.filter(p=>name(p.key)===remove.name).length!==1)continue;
          for(const register of methods){
            if(register.name===remove.name||n.properties.filter(p=>name(p.key)===register.name).length!==1||!listenerRegistration(register.node,certificate))continue;
            const protocol={...certificate,register_method:register.name,remove_method:remove.name};
            listenerMethods.set(remove.node,{...protocol,role:'remove'});
            listenerMethods.set(register.node,{...protocol,role:'register'});
          }
        }
      }
    }
    if(n.type==='VariableDeclarator'||n.type==='AssignmentExpression'){
      const target=n.id||n.left,rhs=n.init||n.right;walk(rhs,ctx,n,'right');
      let call=rhs?.type==='AwaitExpression'?rhs.argument:rhs;
      emit(n,'write',ctx,{target:name(target)||text(target),rhs_callee:['CallExpression','OptionalCallExpression'].includes(call?.type)?name(call.callee):'',awaited:rhs?.type==='AwaitExpression',operator:n.operator||'=',references:[...new Set([...references(target),...references(rhs)])],value_references:references(rhs),rhs_kind:rhs?.type||null,
        ...(n.type==='VariableDeclarator'&&rhs?.type==='Identifier'&&objectBindings(target).length?{object_binding_source:rhs.name,object_bindings:objectBindings(target)}:{}),
        declared_names:n.type==='VariableDeclarator'?boundNames(target):[],assigned_names:boundNames(target),write_roots:writeRoots(target),
        rhs_text:['Identifier','BooleanLiteral','NumericLiteral','StringLiteral','NullLiteral'].includes(rhs?.type)?text(rhs):null});return;
    }
    if(n.type==='UpdateExpression'){
      emit(n,'write',ctx,{target:name(n.argument)||text(n.argument),rhs_callee:'',awaited:false,operator:n.operator,references:references(n.argument),value_references:references(n.argument),rhs_kind:null,
        assigned_names:boundNames(n.argument),write_roots:writeRoots(n.argument),
        update_prefix:!!n.prefix,update_standalone:parent?.type==='ExpressionStatement'});return;
    }
    if(['CallExpression','OptionalCallExpression','NewExpression'].includes(n.type)){
      // The function body of a callback is visited in its own scope, never inlined.
      walk(n.callee,ctx,n,'callee');n.arguments.forEach(a=>walk(a,ctx,n,'arguments'));
      emit(n,'call',ctx,{callee:name(n.callee)||'<dynamic>',receiver:name(n.callee.object),arguments:n.arguments.map(a=>text(a)),optional:n.type==='OptionalCallExpression',construct:n.type==='NewExpression',references:references(n),argument_references:n.arguments.map(references),
        ...(functionScopes.has(n.callee)&&n.type==='CallExpression'?{immediate_target_scope:functionScopes.get(n.callee)}:{})});return;
    }
    if(n.type==='AwaitExpression'||n.type==='YieldExpression'){
      walk(n.argument,ctx,n,'argument');emit(n,n.type==='AwaitExpression'?'await':'yield',ctx);return;
    }
    if(n.type==='ReturnStatement'||n.type==='ThrowStatement'){
      walk(n.argument,ctx,n,'argument');emit(n,n.type==='ReturnStatement'?'return':'raise',ctx,{references:references(n.argument),
        ...(n.type==='ReturnStatement'&&n.argument?.type==='Identifier'?{return_identifier:n.argument.name}:{})});return;
    }
    for(const [k,v] of Object.entries(n)){
      if(syntaxKeys.has(k))continue;
      if(Array.isArray(v))v.forEach(x=>walk(x,ctx,n,k));else if(v&&typeof v==='object')walk(v,ctx,n,k);
    }
  }
  try {
    const ext=file.languageExt || file.path.split('.').pop().toLowerCase();const plugins=[];
    if(['ts','tsx'].includes(ext))plugins.push('typescript');
    if(['js','jsx','tsx','mjs','cjs'].includes(ext))plugins.push('jsx');
    const ast=parser.parse(source,{sourceType:file.scriptBlock?'module':'unambiguous',plugins,errorRecovery:false});
    walk(ast.program,{scope:root,block:root,statement:0,conditions:[]});
    return {path:file.path,language:['ts','tsx'].includes(ext)?'typescript':'javascript',column_unit:'utf16_code_units',status:'parsed',functions,events,imports,exports,bindings};
  } catch(e) { return {path:file.path,language:'javascript/typescript',status:'parse_error',error:{message:String(e.message),line:e.loc?.line||null},functions:[],events:[],imports:[],exports:{},bindings:[]}; }
}
// Stream stdin to handle large piped source inventories without EAGAIN errors.
let inputText='';
process.stdin.setEncoding('utf8');
process.stdin.on('data',chunk=>{inputText+=chunk;});
process.stdin.on('error',e=>{process.stderr.write(String(e.message)+'\n');process.exitCode=2;});
process.stdin.on('end',()=>{
  try {
    const input=JSON.parse(inputText), files=input.files.map(analyze);
    process.stdout.write(JSON.stringify({parser:'@babel/parser',version,library_sha256,node:process.version,
      ...(sfcMetadata?{sfc_parser:sfcMetadata}:{}),files}));
  } catch(e){process.stderr.write(String(e.message)+'\n');process.exitCode=2;}
});

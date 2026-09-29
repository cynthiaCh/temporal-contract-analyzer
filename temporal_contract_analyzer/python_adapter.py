import ast


def analyze(path, source):
    result=dict(path=path,language='python',column_unit='utf8_bytes',status='parsed',functions=[],events=[],imports=[],exports={},bindings=[])
    try: tree=ast.parse(source,filename=path)
    except (SyntaxError,ValueError,RecursionError) as e:
        result.update(status='parse_error',error=dict(message=str(e),line=getattr(e,'lineno',None)));return result
    def text(n): return ast.get_source_segment(source,n) or ''
    def name(n):
        if isinstance(n,ast.Name):return n.id
        if isinstance(n,ast.Attribute):return name(n.value)+'.'+n.attr if name(n.value) else ''
        return ''
    def references(n):
        found={}
        def visit(node):
            if node is None or isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef,ast.Lambda)):return
            if isinstance(node,ast.Name):found[node.id]=None;return
            if isinstance(node,ast.Attribute):
                dotted=name(node)
                if dotted:found[dotted]=None;return
                visit(node.value);return
            # Constants and attribute/keyword names are not references. Child
            # AST nodes include only actual expressions, never those strings.
            for child in ast.iter_child_nodes(node):visit(child)
        visit(n);return list(found)
    def loc(n):return dict(line=getattr(n,'lineno',1),column=getattr(n,'col_offset',0),end_line=getattr(n,'end_lineno',1),end_column=getattr(n,'end_col_offset',0))
    counts={}
    def emit(n,kind,ctx,**fields):
        event=dict(id='e'+str(len(result['events'])),kind=kind,**ctx,**loc(n),text=text(n),**fields);result['events'].append(event)
    def block(nodes,ctx,label):
        for i,n in enumerate(nodes):walk(n,dict(ctx,block=ctx['scope']+'/'+label,statement=i))
    def walk(n,ctx,parent=None,argument_index=None):
        if n is None:return
        if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.Lambda)):
            label=getattr(n,'name','<lambda>');key=ctx['scope']+'/'+label;counts[key]=counts.get(key,0)+1;scope=key+('#'+str(counts[key]) if counts[key]>1 else '')
            args=n.args.posonlyargs+n.args.args+([n.args.vararg] if n.args.vararg else [])+n.args.kwonlyargs+([n.args.kwarg] if n.args.kwarg else [])
            result['functions'].append(dict(id=scope,parent=ctx['scope'],name=label,parameters=[a.arg for a in args],**{'async':isinstance(n,ast.AsyncFunctionDef)},**loc(n)))
            if not isinstance(n,ast.Lambda):
                result['bindings'].append(dict(scope=ctx['scope'],name=label,target=scope))
                if ctx['scope']=='<module>':result['exports'][label]=label
                # Decorators/defaults execute while defining, unlike the function body.
                for d in n.decorator_list:walk(d,ctx)
            for d in n.args.defaults+[x for x in n.args.kw_defaults if x]:walk(d,ctx)
            inner=dict(scope=scope,block=scope+'/body',statement=0,conditions=[])
            if isinstance(n,ast.Lambda):
                # The lambda header can span lines; offsets remain UTF-8 bytes.
                header=ast.copy_location(ast.Pass(),n)
                header.end_lineno=n.body.lineno;header.end_col_offset=n.body.col_offset
                emit(header,'function_definition',inner,name=label)
                if isinstance(parent,ast.Call):emit(header,'callback_argument',ctx,target_scope=scope,callee=name(parent.func) or '<dynamic>',argument_index=argument_index)
            else:
                # Keep the existing bounded, source-exact definition anchor.
                header=source.splitlines()[n.lineno-1].encode('utf-8')[n.col_offset:].decode('utf-8')
                result['events'].append(dict(id='e'+str(len(result['events'])),kind='function_definition',
                    **inner,line=n.lineno,column=n.col_offset,end_line=n.lineno,
                    end_column=n.col_offset+len(header.encode('utf-8')),text=header,name=label))
            if isinstance(n,ast.Lambda):walk(n.body,inner)
            else:block(n.body,inner,'body')
            return
        if isinstance(n,ast.ClassDef):
            # Methods live in a class namespace; this is not an instance dispatch model.
            for d in n.decorator_list+n.bases:walk(d,ctx)
            block(n.body,dict(ctx,scope=ctx['scope']+'/'+n.name),'class-body');return
        if isinstance(n,(ast.Import,ast.ImportFrom)):
            for a in n.names:
                module=a.name if isinstance(n,ast.Import) else '.'*n.level+(n.module or '')
                result['imports'].append(dict(scope=ctx['scope'],local=a.asname or (a.name.split('.')[0] if isinstance(n,ast.Import) else a.name),module=module,symbol='*' if isinstance(n,ast.Import) else a.name,**loc(n)))
            return
        if isinstance(n,ast.If):
            emit(n.test,'guard',ctx,expression=text(n.test),references=references(n.test));walk(n.test,ctx)
            block(n.body,dict(ctx,conditions=ctx['conditions']+['if '+text(n.test)]),'then@'+str(n.lineno))
            block(n.orelse,dict(ctx,conditions=ctx['conditions']+['else of '+text(n.test)]),'else@'+str(n.lineno));return
        if isinstance(n,ast.Try):
            block(n.body,ctx,'try@'+str(n.lineno))
            for h in n.handlers:block(h.body,dict(ctx,conditions=ctx['conditions']+['except '+text(h.type)]),'except@'+str(h.lineno))
            block(n.orelse,dict(ctx,conditions=ctx['conditions']+['try normal completion']),'try-else@'+str(n.lineno))
            block(n.finalbody,dict(ctx,conditions=ctx['conditions']+['finally path']),'finally@'+str(n.lineno));return
        if isinstance(n,(ast.For,ast.AsyncFor,ast.While)):
            if isinstance(n,ast.AsyncFor):emit(n,'async_iteration',ctx)
            walk(getattr(n,'iter',getattr(n,'test',None)),ctx)
            c=dict(ctx,conditions=ctx['conditions']+[type(n).__name__+' path; execution/repetition not proven'])
            body=c
            if isinstance(n,(ast.For,ast.AsyncFor)):
                body=dict(c,loop_bindings=ctx.get('loop_bindings',[])+[dict(target=name(n.target) or text(n.target),iterable=text(n.iter),iterable_references=references(n.iter))])
            block(n.body,body,'loop@'+str(n.lineno));block(n.orelse,c,'loop-else@'+str(n.lineno));return
        if isinstance(n,(ast.With,ast.AsyncWith)):
            for item in n.items:walk(item.context_expr,ctx)
            emit(n,'resource_scope',ctx,asynchronous=isinstance(n,ast.AsyncWith))
            block(n.body,dict(ctx,conditions=ctx['conditions']+['context body after successful entry']),'with@'+str(n.lineno));return
        if isinstance(n,(ast.IfExp,ast.BoolOp,ast.ListComp,ast.SetComp,ast.DictComp,ast.GeneratorExp)):
            c=dict(ctx,block=ctx['scope']+'/conditional@'+str(n.lineno),conditions=ctx['conditions']+[type(n).__name__+' conditional evaluation'])
            for child in ast.iter_child_nodes(n):walk(child,c)
            return
        if isinstance(n,(ast.Assign,ast.AnnAssign,ast.AugAssign)):
            walk(n.value,ctx)
            call=n.value.value if isinstance(n.value,ast.Await) else n.value
            targets=n.targets if isinstance(n,ast.Assign) else [n.target]
            for target in targets:emit(n,'write',ctx,target=name(target) or text(target),rhs_callee=name(call.func) if isinstance(call,ast.Call) else '',awaited=isinstance(n.value,ast.Await),operator='=' if not isinstance(n,ast.AugAssign) else type(n.op).__name__,references=list(dict.fromkeys(references(target)+references(n.value))),value_references=references(n.value),rhs_kind=type(n.value).__name__ if n.value else None)
            return
        if isinstance(n,ast.Call):
            walk(n.func,ctx)
            arguments=n.args+[a.value for a in n.keywords]
            for i,a in enumerate(arguments):walk(a,ctx,n,i)
            emit(n,'call',ctx,callee=name(n.func) or '<dynamic>',receiver=name(n.func.value) if isinstance(n.func,ast.Attribute) else '',arguments=[text(a) for a in arguments],optional=False,construct=False,references=references(n),argument_references=[references(a) for a in arguments]);return
        if isinstance(n,(ast.Await,ast.Yield,ast.YieldFrom)):
            walk(n.value,ctx);emit(n,'await' if isinstance(n,ast.Await) else 'yield',ctx);return
        if isinstance(n,(ast.Return,ast.Raise)):
            for child in ast.iter_child_nodes(n):walk(child,ctx)
            emit(n,'return' if isinstance(n,ast.Return) else 'raise',ctx,references=references(n));return
        for child in ast.iter_child_nodes(n):walk(child,ctx)
    result['functions'].append(dict(id='<module>',parent=None,name='<module>',parameters=[],**{'async':False},line=1,column=0,end_line=len(source.splitlines()),end_column=0))
    block(tree.body,dict(scope='<module>',block='<module>',statement=0,conditions=[]),'body')
    return result

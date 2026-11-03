"""Small dependency-free MCP stdio adapter (2025-06-18), no model calls.

Only initialize/ping/tools are advertised. All results refer to the same archive
as the CLI/editor. A bound research session exposes exactly one frozen layer.
"""
import json
from pathlib import Path
import sys
import uuid

from . import archive
from .core import EvidenceError, VERSION, sha


def tool(name, description, properties, required=(), writes=False):
    return dict(name=name, description=description, inputSchema=dict(type='object', properties=properties,
                required=list(required), additionalProperties=False),
                annotations=dict(readOnlyHint=not writes, destructiveHint=False, openWorldHint=False))


STRING = {'type': 'string'}
LAYERS = ['full', 'none', 'locations', 'facts', 'review', 'audit', 'risk', 'audit_review']
TOOLS = [
    tool('scan_project', 'Scan a saved candidate directory or source file and archive exact inputs. Returns report_id; use read_report next. Findings are review hints, not proven bugs.',
         {k: STRING for k in ('path', 'project', 'label', 'task_id', 'parent_report_id')}, ['path'], writes=True),
    tool('list_reports', 'Find archived reports. This is an index, not evidence that an agent previously received a report.',
         dict(search=STRING, project=STRING, status=STRING, origin=STRING,
              limit={'type': 'integer', 'minimum': 1, 'maximum': 100}, offset={'type': 'integer', 'minimum': 0})),
    tool('read_report', 'Read an exact archived report/layer in character pages. Follow next_offset until null. Each response records its exact delivered material; transport success does not prove model use.',
         dict(report_id=STRING, layer={'type': 'string', 'enum': LAYERS},
              offset={'type': 'integer', 'minimum': 0}, limit={'type': 'integer', 'minimum': 1, 'maximum': 20000}), ['report_id'], writes=True),
    tool('read_source', 'Read a page of the archived source snapshot, which may differ from today’s working tree.',
         dict(report_id=STRING, path=STRING, offset={'type': 'integer', 'minimum': 0},
              limit={'type': 'integer', 'minimum': 1, 'maximum': 20000}), ['report_id', 'path'], writes=True),
    tool('read_context', 'Read a paginated JSON context packet: finding evidence plus candidate lexical/import definitions from the same archived snapshot. Includes reasons and unresolved gaps. Follow next_offset. Not a bug verdict or complete dependency analysis; separate from frozen experiment layers.',
         dict(report_id=STRING, finding_id=STRING,
              depth={'type': 'integer', 'minimum': 0, 'maximum': 5},
              max_chars={'type': 'integer', 'minimum': 1, 'maximum': 100000},
              aliases={'type': 'object', 'additionalProperties': STRING, 'maxProperties': 100},
              offset={'type': 'integer', 'minimum': 0},
              limit={'type': 'integer', 'minimum': 1, 'maximum': 20000}), ['report_id'], writes=True),
    tool('compare_reports', 'Compare two reports from the same project and scope. Changed hints do not establish bug introduction or repair.',
         dict(before_id=STRING, after_id=STRING), ['before_id', 'after_id']),
]


def validate(definition, args):
    schema = definition['inputSchema']
    if not isinstance(args, dict) or set(args) - set(schema['properties']) or set(schema['required']) - set(args):
        raise EvidenceError('Invalid tool arguments')
    for key, value in args.items():
        prop = schema['properties'][key]
        if prop['type'] == 'string' and (not isinstance(value, str) or len(value) > 4096):
            raise EvidenceError('Invalid string: ' + key)
        if prop['type'] == 'integer' and (type(value) is not int or value < prop.get('minimum', 0) or value > prop.get('maximum', 10**9)):
            raise EvidenceError('Invalid integer: ' + key)
        if prop['type'] == 'object' and (not isinstance(value, dict) or len(value)>prop.get('maxProperties',100)
                or any(not isinstance(k,str) or not isinstance(v,str) or len(k)>4096 or len(v)>4096 for k,v in value.items())):
            raise EvidenceError('Invalid object: ' + key)
        if 'enum' in prop and value not in prop['enum']:
            raise EvidenceError('Invalid choice: ' + key)


class Session:
    def __init__(self, store=None, node=None, report_id=None, layer=None):
        self.store = archive.store_path(store)
        self.node = node
        self.report_id, self.layer = report_id, layer
        if bool(report_id) != bool(layer):
            raise EvidenceError('Research binding requires both --report-id and --layer')
        if report_id:
            if layer == 'full':
                raise EvidenceError('Research binding requires a frozen layer, not the full report')
            archive.layer_text(report_id, layer, self.store)
        self.initialized = False
        self.ready = False
        self.session_id = uuid.uuid4().hex
        self.client = {}
        self.pending_delivery = None
        self.context_cache = {}

    def definitions(self):
        if self.report_id:
            return [tool('read_report', 'Read the one frozen material assigned to this research session. No other reports, layers or source snapshots are exposed.',
                         dict(offset={'type': 'integer', 'minimum': 0}, limit={'type': 'integer', 'minimum': 1, 'maximum': 20000}), writes=True)]
        return TOOLS

    def page(self, report_id, text, offset, limit, material):
        if offset > len(text):
            raise EvidenceError('Offset beyond material length')
        chunk = text[offset:offset+limit]
        delivery_id = uuid.uuid4().hex
        result = dict(report_id=report_id, material=material, text=chunk, offset=offset,
                      next_offset=offset+len(chunk) if offset+len(chunk) < len(text) else None,
                      total_characters=len(text), material_sha256=sha(text.encode('utf-8')),
                      response_text_sha256=sha(chunk.encode('utf-8')), delivery_id=delivery_id)
        archive.append_record('deliveries', report_id,
                              dict(delivery_id=delivery_id, state='prepared_for_tool_response', session_id=self.session_id,
                                   client=self.client, payload=result, qualification='Prepared, not yet confirmed written to transport'), self.store)
        self.pending_delivery = dict(report_id=report_id, delivery_id=delivery_id, session_id=self.session_id)
        return result

    def call(self, name, args):
        definition = next((t for t in self.definitions() if t['name'] == name), None)
        if not definition:
            raise EvidenceError('Unknown or unavailable tool')
        validate(definition, args)
        if name == 'scan_project':
            if not Path(args['path']).is_absolute():
                raise EvidenceError('scan_project requires an absolute candidate path')
            labels = {k: v for k, v in args.items() if k != 'path'}
            return archive.scan_path(args['path'], self.store, self.node, 'codex', **labels)['archive']
        if name == 'list_reports':
            return archive.list_reports(self.store, **args)
        if name == 'read_report':
            report_id = self.report_id or args['report_id']
            layer = self.layer or args.get('layer', 'full')
            return self.page(report_id, archive.layer_text(report_id, layer, self.store),
                             args.get('offset', 0), args.get('limit', 12000), layer)
        if name == 'read_source':
            source = archive.read_source(args['report_id'], args['path'], self.store)
            return self.page(args['report_id'], source['text'], args.get('offset', 0), args.get('limit', 12000), 'source:'+args['path'])
        if name == 'read_context':
            from .context import build_context
            options = {k:v for k,v in args.items() if k not in {'offset','limit'}}
            key = json.dumps(options, sort_keys=True, ensure_ascii=False)
            if key not in self.context_cache:
                packet = build_context(store=self.store, node=self.node, **options)
                if len(self.context_cache)>=4:
                    self.context_cache.pop(next(iter(self.context_cache)))
                self.context_cache[key] = json.dumps(packet, ensure_ascii=False, indent=2)+'\n'
            return self.page(args['report_id'], self.context_cache[key], args.get('offset',0),
                             args.get('limit',12000), 'context:'+sha(key.encode('utf-8')))
        if name == 'compare_reports':
            return archive.compare_reports(args['before_id'], args['after_id'], self.store)
        raise EvidenceError('Unknown tool')

    def handle(self, request):
        self.pending_delivery = None
        if not isinstance(request, dict) or request.get('jsonrpc') != '2.0' or not isinstance(request.get('method'), str):
            return dict(jsonrpc='2.0', id=request.get('id') if isinstance(request, dict) else None,
                        error=dict(code=-32600, message='Invalid request'))
        method, params = request['method'], request.get('params', {})
        if 'id' not in request:
            if method == 'notifications/initialized' and self.initialized:
                self.ready = True
            return None
        response = dict(jsonrpc='2.0', id=request['id'])
        if not isinstance(params, dict):
            return dict(response, error=dict(code=-32602, message='Expected params object'))
        if method == 'initialize':
            if self.initialized:
                return dict(response, error=dict(code=-32600, message='Already initialized'))
            self.initialized = True
            self.client = params.get('clientInfo', {})
            requested = params.get('protocolVersion')
            version = requested if requested in {'2024-11-05', '2025-03-26', '2025-06-18'} else '2025-06-18'
            return dict(response, result=dict(protocolVersion=version, capabilities={'tools': {'listChanged': False}},
                        serverInfo={'name': 'temporal-contracts', 'version': VERSION},
                        instructions='Use archived evidence as incomplete review hints. Scan first, read the report by ID, verify source and behavior, then test changes. Never treat zero hints as proof of safety.'))
        if method == 'ping':
            return dict(response, result={})
        if not self.ready:
            return dict(response, error=dict(code=-32600, message='Initialize the session first'))
        if method == 'tools/list':
            return dict(response, result={'tools': self.definitions()})
        if method == 'tools/call':
            try:
                value = self.call(params.get('name'), params.get('arguments', {}))
                return dict(response, result=dict(content=[{'type': 'text', 'text': json.dumps(value, ensure_ascii=False)}], isError=False))
            except (EvidenceError, OSError, ValueError, KeyError, TypeError) as error:
                return dict(response, result=dict(content=[{'type': 'text', 'text': str(error)}], isError=True))
        return dict(response, error=dict(code=-32601, message='Method not found'))

    def written(self):
        if self.pending_delivery:
            item = self.pending_delivery
            archive.append_record('deliveries', item['report_id'], dict(item, state='transport_written',
                                  qualification='Server wrote the tool response; client receipt, model attention and use remain unconfirmed'), self.store)
            self.pending_delivery = None


def serve(store=None, node=None, report_id=None, layer=None):
    session = Session(store, node, report_id, layer)
    while True:
        line = sys.stdin.buffer.readline(1024*1024+1)
        if not line:
            return
        if len(line) > 1024*1024:
            raise EvidenceError('MCP request exceeds 1 MiB')
        try:
            response = session.handle(json.loads(line))
        except (ValueError, UnicodeError):
            response = dict(jsonrpc='2.0', id=None, error=dict(code=-32700, message='Invalid JSON'))
        if response is not None:
            try:
                sys.stdout.write(json.dumps(response, ensure_ascii=False) + '\n')
                sys.stdout.flush()
                session.written()
            except BrokenPipeError:
                return
            except OSError as error:
                print('Could not persist delivery receipt: ' + str(error), file=sys.stderr)

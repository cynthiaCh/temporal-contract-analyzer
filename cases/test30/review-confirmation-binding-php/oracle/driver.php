<?php
require $argv[1].'/src/workflow.php';
function emit($value) { echo json_encode($value)."\n"; flush(); }
class Environment {
    public $store, $archive;
    private $callbacks=[], $serial=0, $workspace, $preview;
    function __construct() { $this->archive=new Archive(); }
    function call($kind, ...$args) {
        emit(['call'=>$kind, 'args'=>$args]);
        while (($line=fgets(STDIN)) !== false) {
            $message=json_decode($line, true);
            if (array_key_exists('reply', $message)) return $message['reply'];
            $this->dispatch($message);
        }
        throw new Exception('RPC EOF');
    }
    function schedule($fn, $delay) {
        $id=++$this->serial; $this->callbacks[$id]=$fn;
        return $this->call('schedule', $id, $delay);
    }
    function cancel($handle) { $this->call('cancel', $handle); }
    function output($kind, $value) { $this->call($kind, $value); }
    function write($id, $text) { return $this->call('write', $id, $text); }
    function capture($snapshot) { return $this->call('capture', $snapshot); }
    function dispatch($message) {
        $method=$message['method']; $a=$message['args']; $result=null;
        switch ($method) {
            case 'storeInit': $this->store=new Store($a[0]); break;
            case 'storeRead': $result=$this->store->read(...$a); break;
            case 'storeWrite': $result=$this->store->write(...$a); break;
            case 'storeSubscribe': $result=$this->store->subscribe(function($event) use ($a) { $this->call('subscriber', $a[0], $event); }); break;
            case 'storeUnsubscribe': $this->store->stop(...$a); break;
            case 'archiveCapture': $result=$this->archive->capture(...$a); break;
            case 'archiveSubscribe':$result=$this->archive->subscribe(function($event)use($a){$this->call('subscriber',$a[0],$event);});break;
            case 'archiveUnsubscribe':$this->archive->stop(...$a);break;
            case 'archiveList': $result=$this->archive->all(); break;
            case 'init': $this->workspace=new Workspace($this); break;
            case 'previewInit': $this->preview=new Preview($this); break;
            case 'previewQuery': $this->preview->query(...$a); break;
            case 'previewHide': $this->preview->hide(); break;
            case 'invoke': $fn=$this->callbacks[$a[0]]; unset($this->callbacks[$a[0]]); $fn(); break;
            default: $result=$this->workspace->$method(...$a);
        }
        emit(['result'=>$result]);
    }
}
$env=new Environment();
while (($line=fgets(STDIN)) !== false) $env->dispatch(json_decode($line, true));

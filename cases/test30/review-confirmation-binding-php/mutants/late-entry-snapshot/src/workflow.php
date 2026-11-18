<?php
// Claim sessions keep their own callable and text; controller owns acceptance.
class Store {
    private $records, $listeners = [], $serial = 0, $revision = 0;
    function __construct($records) { $this->records = $records; }
    function read($id) { return $this->records[$id] ?? ''; }
    function subscribe($fn) { $token = ++$this->serial; $this->listeners[$token] = $fn; return $token; }
    function stop($token) { unset($this->listeners[$token]); }
    function write($id, $text) {
        $this->records[$id] = $text;
        $event = ['id'=>$id, 'text'=>$text, 'revision'=>++$this->revision];
        foreach(array_keys($this->listeners)as $token)if(isset($this->listeners[$token]))($this->listeners[$token])($event);
        return $event;
    }
}
class Archive {
    private $receipts = [],$listeners=[],$serial=0;
    function capture($snapshot) {
        $receipt = ['id'=>$snapshot['id'], 'text'=>$snapshot['text']];
        $this->receipts[] = $receipt;
        foreach(array_keys($this->listeners)as $token)if(isset($this->listeners[$token]))($this->listeners[$token])($receipt);
        return $receipt;
    }
    function subscribe($fn){$token=++$this->serial;$this->listeners[$token]=$fn;return $token;}
    function stop($token){unset($this->listeners[$token]);}
    function all() { return $this->receipts; }
}
class Trailing {
    private $env, $delay, $work, $handle = null, $pending = null;
    function __construct($env, $delay, $work) { $this->env=$env; $this->delay=$delay; $this->work=$work; }
    function push($value) {
        if ($this->handle !== null) $this->env->cancel($this->handle);
        $this->pending=$value;
        $this->handle=$this->env->schedule(function() { $this->flush(); }, $this->delay);
    }
    function flush() {
        if ($this->handle !== null) $this->env->cancel($this->handle);
        $value=$this->pending; $this->pending=null; $this->handle=null;
        if ($value !== null) ($this->work)($value);
    }
    function cancel() {
        if ($this->handle !== null) $this->env->cancel($this->handle);
        $this->pending=null; $this->handle=null;
    }
}
class Confirmation {
    private $current,$emit,$owner;
    function __construct($current,$emit){$this->current=$current;$this->emit=$emit;$this->owner=$current();}
    function active(){return $this->owner!==null&&$this->owner===($this->current)();}
    function show($receipt){if($this->active())($this->emit)($receipt);}
}
class ClaimVisit {
    public $id, $text, $token, $task;
    function __construct($id, $text, $token, $task) {
        $this->id=$id; $this->text=$text; $this->token=$token; $this->task=$task;
    }
}
class Workspace {
    private $env, $current=null, $navigation=0;
    function __construct($env) { $this->env=$env; }
    private function retire() {
        $leaving=$this->current; $this->current=null;
        if ($leaving !== null) $this->env->store->stop($leaving->token);
        $this->env->output('document', null);
        if ($leaving !== null) $leaving->task->flush();
    }
    function open($id) {
        $this->env->output('notice', null); $request=++$this->navigation;
        $this->retire();
        if ($request !== $this->navigation) return;
        $token=$this->env->store->subscribe(function($event) use ($id) {
            if ($event['id'] === $id) $this->env->output('status', $event);
        });
        $task=new Trailing($this->env, 120, function($text) use ($id) { $this->env->write($id, $text); });
        $this->current=new ClaimVisit($id, $this->env->store->read($id), $token, $task);
        $this->env->output('document', ['id'=>$id, 'text'=>$this->current->text]);
    }
    function edit($text) {
        if ($this->current === null) return;
        $this->current->text=$text;
        $this->current->task->push($text);
    }
    function close() { $this->env->output('notice', null); ++$this->navigation; $this->retire(); }
    function submit() {
        $confirmation=new Confirmation(function(){return $this->current;},function($receipt){$this->env->output('notice',$receipt);});
        $visit=$this->current;
        if ($visit === null) return null;
        $snapshot=['id'=>$visit->id, 'text'=>$visit->text];
        $visit->task->flush();
        
        
        $snapshot=['id'=>$visit->id,'text'=>$visit->text];
        $receipt=$this->env->capture($snapshot);
        
        $confirmation->show($receipt);
        return $receipt;
    }
    function dispose() { $this->close(); }
}
class Preview {
    private $task;
    function __construct($env) {
        $this->task=new Trailing($env, 40, function($query) use ($env) { $env->output('preview', ['query'=>$query]); });
    }
    function query($text) { $this->task->push($text); }
    function hide() { $this->task->cancel(); }
}

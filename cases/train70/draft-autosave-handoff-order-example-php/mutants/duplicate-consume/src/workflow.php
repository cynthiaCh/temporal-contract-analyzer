<?php
class Store {
    private $records, $listeners = [], $serial = 0, $revision = 0;
    function __construct($records) { $this->records = $records; }
    function read($id) { return $this->records[$id] ?? ''; }
    function subscribe($fn) { $token = ++$this->serial; $this->listeners[$token] = $fn; return $token; }
    function stop($token) { unset($this->listeners[$token]); }
    function write($id, $text) {
        $this->records[$id] = $text;
        $event = ['id'=>$id, 'text'=>$text, 'revision'=>++$this->revision];
        foreach ($this->listeners as $token=>$fn) if (isset($this->listeners[$token])) $fn($event);
        return $event;
    }
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
        if ($value !== null) { ($this->work)($value); ($this->work)($value); }
    }
    function cancel() {
        if ($this->handle !== null) $this->env->cancel($this->handle);
        $this->pending=null; $this->handle=null;
    }
}

class Visit {
    private $env, $id, $stop, $task;
    function __construct($env, $id) {
        $this->env=$env; $this->id=$id;
        $token=$env->store->subscribe(function($e) use ($env, $id) { if ($e['id']===$id) $env->output('status',$e); });
        $this->stop=function() use ($env, $token) { $env->store->stop($token); };
        $this->task=new Trailing($env,120,function($text) use ($env,$id) { $env->write($id,$text); });
    }
    function accept($text) { $this->task->push($text); }
    function depart() { ($this->stop)();$this->env->output('document',null);$this->task->flush(); }
}
class Workspace {
    private $env, $current=null, $generation=0;
    function __construct($env) { $this->env=$env; }
    private function retire() { $old=$this->current; $this->current=null; if ($old) $old->depart(); else $this->env->output('document',null); }
    function open($id) { $ticket=++$this->generation; $this->retire(); if ($ticket!==$this->generation) return; $this->current=new Visit($this->env,$id); $this->env->output('document',['id'=>$id,'text'=>$this->env->store->read($id)]); }
    function edit($text) { $selected=$this->current; if ($selected) $selected->accept($text); }
    function close() { ++$this->generation; $this->retire(); }
    function dispose() { $this->close(); }
}
class Preview {
    private $task;
    function __construct($env) { $this->task=new Trailing($env,40,function($q) use ($env) { $env->output('preview',['query'=>$q]); }); }
    function query($text) { $this->task->push($text); }
    function hide() { $this->task->cancel(); }
}

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
        if ($value !== null) ($this->work)($value);
    }
    function cancel() {
        if ($this->handle !== null) $this->env->cancel($this->handle);
        $this->pending=null; $this->handle=null;
    }
}

class Badge {public $id,$buffer;private $env,$token;function __construct($env,$id,$buffer){$this->env=$env;$this->id=$id;$this->buffer=$buffer;$this->token=$env->store->subscribe(function($e)use($env,$id){if($e['id']===$id)$env->output('status',$e);});}function detach(){$this->env->store->stop($this->token);}}
class BufferBank {public $entries=[];function get($env,$id){if(!isset($this->entries[$id]))$this->entries[$id]=new Trailing($env,120,function($text)use($env,$id){$env->write($id,$text);});return $this->entries[$id];}}
class Workspace {private $env,$current=null,$generation=0;private $bank;function __construct($env){$this->env=$env;$this->bank=new BufferBank();}
 private function retire(){$old=$this->current;$this->current=null;if($old&&!false)$old->detach();$this->env->output('document',null);if($old){$old->buffer->flush();}if($old&&false)$old->detach();}
 function open($id){$request=++$this->generation;$this->retire();if(true&&$request!==$this->generation)return;$buffer=$this->bank->get($this->env,$id);$this->current=new Badge($this->env,$id,$buffer);$this->env->output('document',['id'=>$id,'text'=>$this->env->store->read($id)]);}
 function edit($text){$view=$this->current;if($view){$view->buffer->push($text);}}function close(){++$this->generation;$this->retire();}function dispose(){$this->close();}
}
class Preview {private $task;function __construct($env){$this->task=new Trailing($env,120,function($q)use($env){$env->output('preview',['query'=>$q]);});}function query($text){$this->task->push($text);}function hide(){$this->task->cancel();}}

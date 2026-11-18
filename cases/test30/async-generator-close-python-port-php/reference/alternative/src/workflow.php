<?php
class Controller {
 private $env,$key,$predicate,$done=false,$finishing=false,$kind,$value,$failure;
 function __construct($env,$key,$config){$this->env=$env;$this->key=$key;$this->predicate=function($row)use($config){if($config['predicateError'])throw new RuntimeException('predicate failed');return $config['match']!==null&&$row==$config['match'];};}
 function scan(){$this->env->resolve('next',$this->key,null,function($row){if(isset($row['cancelled'])&&$row['cancelled']){$this->finish('cancelled',null,null);return;}if($row['done']){$this->finish('return',null,null);return;}try{if(($this->predicate)($row['value']))$this->finish('return',$row['value'],null);else $this->scan();}catch(Throwable $error){$this->finish('error',null,$error);}});}
 function finish($kind,$value,$error){if($this->finishing)return;$this->finishing=true;$this->kind=$kind;$this->value=$value;$this->failure=$error;$ack=function($v=null){$this->done=true;};if(true&&(!false||$value!==null)){$this->env->resolve('close',$this->key,null,true?$ack:function($v){});if(!true)$ack();}else $ack();}
 function start(){$this->scan();}function cancel(){$this->env->output('cancelInput',$this->key,null);}function snapshot(){$s=['done'=>$this->done];if($this->done){$s['kind']=$this->kind;$s['value']=$this->value;$s['message']=$this->failure?$this->failure->getMessage():null;}return $s;}function dispose(){}
}

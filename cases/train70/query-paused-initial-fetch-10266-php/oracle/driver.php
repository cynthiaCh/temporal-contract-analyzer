<?php
require $argv[1].'/src/workflow.php';$callbacks=[];$sessions=[];$serial=0;
function send($value){echo json_encode($value,JSON_UNESCAPED_UNICODE|JSON_THROW_ON_ERROR)."\n";flush();}
class Env{private $w;function __construct($w){$this->w=$w;}function bind($fn){global $serial,$callbacks;$callbacks[++$serial]=$fn;return $serial;}function call($name,...$args){send(['call'=>$name,'args'=>array_merge([$this->w],$args)]);while(true){$m=json_decode(fgets(STDIN),true,512,JSON_THROW_ON_ERROR);if(array_key_exists('reply',$m))return $m['reply'];answer($m);}}}
function dispatch($m){global $callbacks,$sessions;$name=$m['method'];$a=$m['args'];if($name==='invoke')return $callbacks[$a[0]]($a[1]);if($name==='init'){$sessions[$a[0]]=new Session(new Env($a[0]),$a[1]);return null;}return $sessions[$a[0]]->handle($name,array_slice($a,1));}
function answer($m){send(['result'=>dispatch($m)]);}
while(($line=fgets(STDIN))!==false)answer(json_decode($line,true,512,JSON_THROW_ON_ERROR));

<?php
require $argv[1].'/src/workflow.php';
$telemetry=[];$callbacks=[];$sessions=[];$handles=[];$files=[];$serial=0;
function send($v){echo json_encode($v,JSON_UNESCAPED_UNICODE)."\n";flush();}
class Env {
 public $w;function __construct($w){$this->w=$w;}
 function bind($fn){global $serial,$callbacks;$callbacks[++$serial]=$fn;return $serial;}
 function call($name,...$args){send(['call'=>$name,'args'=>array_merge([$this->w],$args)]);while(true){$m=json_decode(fgets(STDIN));if(property_exists($m,'reply'))return $m->reply;answer($m);}}
}
function fileObject($v){global $files;if(!isset($files[$v->token]))$files[$v->token]=$v;return $files[$v->token];}
function remember($w,$h){global $handles;if(!$h)return null;$handles[$w.':'.$h->number]=$h;return $h->number;}
function dispatch($m){global $callbacks,$sessions,$handles,$telemetry;$name=$m->method;$a=$m->args;
 if($name==='invoke'){($callbacks[$a[0]])($a[1]);return null;}$w=$a[0];
 if($name==='telemetryStart'){$telemetry[$w]=new Telemetry(new Env($w),fileObject($a[1]));return null;}
 if($name==='telemetryStop'){($telemetry[$w]->stop)();return null;}
 if($name==='init'){$sessions[$w]=new Session(new Env($w));return null;}
 if($name==='standalone')return remember($w,new Attempt(new Env($w),fileObject($a[1]),$a[2]));
 if($name==='cancelHandle'){$handles[$w.':'.$a[1]]->cancel();return null;}
 if($name==='select')return remember($w,$sessions[$w]->select(fileObject($a[1])));
 if($name==='retry')return remember($w,$sessions[$w]->retry());
 return $sessions[$w]->$name();
}
function answer($m){send(['result'=>dispatch($m)]);}
while(($line=fgets(STDIN))!==false)answer(json_decode($line));

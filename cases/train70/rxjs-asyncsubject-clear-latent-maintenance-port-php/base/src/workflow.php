<?php
class Controller{private $state=['value'=>0,'present'=>false,'completed'=>false];function __construct($env,$key,$config){}function get($name){return $this->state[$name];}function set($name,$value){$this->state[$name]=$value;}function clear($closed,$stopped){}function dispose(){}}

define("ace/keyboard/keybinding/emacs",["require","exports","module","ace/keyboard/state_handler"],function(a,b,c){var d=a("../state_handler").StateHandler,e=a("../state_handler").matchCharacterOnly,f={start:[{key:"ctrl-x",then:"c-x"},{regex:["(?:command-([0-9]*))*","(down|ctrl-n)"],exec:"golinedown",params:[{name:"times",match:1,type:"number",defaultValue:1}]},{regex:["(?:command-([0-9]*))*","(right|ctrl-f)"],exec:"gotoright",params:[{name:"times",match:1,type:"number",defaultValue:1}]},{regex:["(?:command-([0-9]*))*","(up|ctrl-p)"],exec:"golineup",params:[{name:"times",match:1,type:"number",defaultValue:1}]},{regex:["(?:command-([0-9]*))*","(left|ctrl-b)"],exec:"gotoleft",params:[{name:"times",match:1,type:"number",defaultValue:1}]},{comment:"This binding matches all printable characters except numbers as long as they are no numbers and print them n times.",regex:["(?:command-([0-9]*))","([^0-9]+)*"],match:e,exec:"inserttext",params:[{name:"times",match:1,type:"number",defaultValue:"1"},{name:"text",match:2}]},{comment:"This binding matches numbers as long as there is no meta_number in the buffer.",regex:["(command-[0-9]*)*","([0-9]+)"],match:e,disallowMatches:[1],exec:"inserttext",params:[{name:"text",match:2,type:"text"}]},{regex:["command-([0-9]*)","(command-[0-9]|[0-9])"],comment:"Stops execution if the regex /meta_[0-9]+/ matches to avoid resetting the buffer."}],"c-x":[{key:"ctrl-g",then:"start"},{key:"ctrl-s",exec:"save",then:"start"}]};b.Emacs=new d(f)}),define("ace/keyboard/state_handler",["require","exports","module"],function(a,b,c){function e(a){this.keymapping=this.$buildKeymappingRegex(a)}var d=!1;e.prototype={$buildKeymappingRegex:function(a){for(var b in a)this.$buildBindingsRegex(a[b]);return a},$buildBindingsRegex:function(a){a.forEach(function(a){a.key?a.key=new RegExp("^"+a.key+"$"):Array.isArray(a.regex)?("key"in a||(a.key=new RegExp("^"+a.regex[1]+"$")),a.regex=new RegExp(a.regex.join("")+"$")):a.regex&&(a.regex=new RegExp(a.regex+"$"))})},$composeBuffer:function(a,b,c,d){if(a.state==null||a.buffer==null)a.state="start",a.buffer="";var e=[];b&1&&e.push("ctrl"),b&8&&e.push("command"),b&2&&e.push("option"),b&4&&e.push("shift"),c&&e.push(c);var f=e.join("-"),g=a.buffer+f;b!=2&&(a.buffer=g);var h={bufferToUse:g,symbolicName:f};return d&&(h.keyIdentifier=d.keyIdentifier),h},$find:function(a,b,c,e,f,g){var h={};return this.keymapping[a.state].some(function(i){var j;if(i.key&&!i.key.test(c))return!1;if(i.regex&&!(j=i.regex.exec(b)))return!1;if(i.match&&!i.match(b,e,f,c,g))return!1;if(i.disallowMatches)for(var k=0;k<i.disallowMatches.length;k++)if(!!j[i.disallowMatches[k]])return!1;if(i.exec){h.command=i.exec;if(i.params){var l;h.args={},i.params.forEach(function(a){a.match!=null&&j!=null?l=j[a.match]||a.defaultValue:l=a.defaultValue,a.type==="number"&&(l=parseInt(l)),h.args[a.name]=l})}a.buffer=""}return i.then&&(a.state=i.then,a.buffer=""),h.command==null&&(h.command="null"),d&&console.log("KeyboardStateMapper#find",i),!0}),h.command?h:(a.buffer="",!1)},handleKeyboard:function(a,b,c,e,f){if(b==0||c!=""&&c!=String.fromCharCode(0)){var g=this.$composeBuffer(a,b,c,f),h=g.bufferToUse,i=g.symbolicName,j=g.keyIdentifier;return g=this.$find(a,h,i,b,c,j),d&&console.log("KeyboardStateMapper#match",h,i,g),g}return null}},b.matchCharacterOnly=function(a,b,c,d){return b==0?!0:b==4&&c.length==1?!0:!1},b.StateHandler=e})
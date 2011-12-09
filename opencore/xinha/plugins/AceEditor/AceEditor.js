function AceEditor(editor) {
    // Keep a copy of the editor to perform any necessary functions
    var editor = editor;
    editor.ace = null;
    var HtmlMode;

    var loader = Xinha.includeAssets();
    if( typeof ace === "undefined" ) {
	loader.loadScript("ace/ace.js", "AceEditor");
	loader.loadScript("ace/mode-html.js", "AceEditor");
        loader.loadScript("ace/theme-idle_fingers.js", "AceEditor"); 
    };


    this.onBeforeMode = function(mode) {
        var parentEl = editor._textArea.parentNode;
        if( mode == "textmode" ) { 
	    return false;
	}
	var html = editor.ace.getSession().getValue();
        editor._textArea.value = html;
	// if we're toggling back to WYSIWYG, 
	// make sure to delete any ACE DIVs
	// and shut down the ACE editor.
	var aces = parentEl.getElementsByClassName("xinha-ace-editor");
	for( var i=0; i<aces.length; ++i ) {
	    parentEl.removeChild(aces[i]);
	}
    };
    this.onMode = function(mode) {
        var parentEl = editor._textArea.parentNode;
        if( mode == "wysiwyg" ) { 
	    return false;
	}
	editor._textArea.style.display = 'none';
        var div = document.createElement("div");
	div.textContent = editor._textarea.value;
	div.id = editor._textArea.id + "-xinha-ace-editor";
        div.className = "xinha-ace-editor";
	div.style.width = editor._textArea.style.width;
	div.style.height = editor._textArea.style.height;
	div.style.position = "relative";
        parentEl.appendChild(div);
	editor.ace = ace.edit(div.id);
        editor.ace.setTheme("ace/theme/idle_fingers");
	editor.ace.setShowPrintMargin(false);
	var HtmlMode = require("ace/mode/html").Mode;
	editor.ace.getSession().setMode(new HtmlMode());
    };
    this.onBeforeSubmit = function() {
        bypass = true;
    }

    // Setup to be called when the plugin is loaded.
    this.onGenerate = function() {
        editor.whenDocReady(function () {
		return;
        });
    }

}

// An object containing metadata for this plugin
AceEditor._pluginInfo = {
    name:'AceEditor',
    version:'0.1',
    developer:'Ethan Jucovy',
    developer_url:'http://www.coactivate.org',
    c_owner:'Ethan Jucovy',
    sponsor:'Coactivate.org',
    sponsor_url:'http://www.coactivate.org',
    license:'GPLv3'
}

function SidebarFormatblock(editor) {
    this.editor = editor;

    var xinha_config = editor.config;
    xinha_config.formatblock = {
	'Normal': 'nosidebar',
	'Heading': 'h2',
	'Subheading': 'h3',
	'Pre-formatted': 'pre',
	'Sidebar': 'sidebar'
    };
    
    xinha_config.formatblockDetector['nosidebar'] = function() {
	return false;
    };
    xinha_config.formatblockDetector['sidebar'] = SidebarFormatblock.detectSidebar;
    
};

SidebarFormatblock._pluginInfo = {
    name:          "SidebarFormatblock",
    version:       "0.1",
    developer:     "OpenCore developers",
    developer_url: "http://www.coactivate.org/projects/opencore",
    c_owner:       "Ethan Jucovy",
    license:       "htmlarea"
};

SidebarFormatblock.execNoSidebar = function (xinha) {
    var blockquote = null
    var firstparent = xinha.getParentElement();
    if (firstparent.tagName != 'H2' &&
        firstparent.tagName != 'H3' && firstparent.tagName != 'PRE') {
        blockquote = firstparent;
        while (blockquote !== null && blockquote.className.trim() != 'pullquote') {
            blockquote = blockquote.parentNode;
        }
    }
    if (blockquote) {
        var blockParent = blockquote.parentNode;
        var firstChild = null;
        while (blockquote.childNodes.length) {
            if (firstChild === null) {
                firstChild = blockquote.childNodes[0];
            }
            blockParent.insertBefore(blockquote.childNodes[0], blockquote);
        }
        blockParent.removeChild(blockquote);
        if (firstChild !== null) {
            // FIXME: this selects the entire first node, instead of just placing the                                                                                                                
            // cursor at the beginning (or at the previous location where the cursor was).                                                                                                           
            // Without this, the cursor hangs off to the side of the screen, where the                                                                                                               
            // blockquote once had been.                                                                                                                                                             
            xinha.selectNodeContents(firstChild);
        }
    } else {
        if( !Xinha.is_gecko) {
            xinha.execCommand('formatblock', false, '<p>');
        } else {
            xinha.execCommand('formatblock', false, 'p');
        }
    }
};

SidebarFormatblock.execSidebar = function( xinha ) {
    var el = xinha.getParentElement();
    if (el.tagName.toUpperCase() == 'BODY') {
        //put div around selection                                                                                                                                                                   
        if (xinha.hasSelectedText()){
            selhtml = xinha.getSelectedHTML();
            newhtml = '<div class="pullquote">' + selhtml + '</div>';
            xinha.insertHTML(newhtml);
        }
    } else {
        //put div around current block                                                                                                                                                               
        while (el !== null & !Xinha.isBlockElement(el)) {
            el = el.parentNode;
        }
        if (el) {
            el_parent = el.parentNode;
            div = xinha._doc.createElement('div');
            div.className = "pullquote";
            el_parent.replaceChild(div, el);
            div.appendChild(el);
        }
    }
    xinha.updateToolbar()
};

SidebarFormatblock.detectSidebar = function(xinha, el) {
    while (el !== null) {
	if (el.nodeType == 1 && el.tagName.toUpperCase() == 'DIV') {
	    return /\bpullquote\b/.test(el.className);
	}
	el = el.parentNode;
    }
    return false;
};


SidebarFormatblock.prototype.onExecCommand = function(cmdID, UI, param) {
    if( cmdID != 'formatblock' ) {
	return false;
    }
    if( param != '<nosidebar>' && param != '<sidebar>' ) {
	return false;
    }
    if( param == '<nosidebar>' ) {
	SidebarFormatblock.execNoSidebar(this.editor);
	return true;
    }
    if( param == '<sidebar>' ) {
	SidebarFormatblock.execSidebar(this.editor);
	return true;
    }
};

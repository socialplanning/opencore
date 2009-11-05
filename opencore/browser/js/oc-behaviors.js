/* Behaviors */

/*
  #
  # OC object - black magic
  #
*/
// Singleton for use throughout
if (typeof OC == "undefined") { 
    var OC = {}
}

// where we'll store all our live elementshist
OC.liveElements = {};

/* 
   #
   # how we know which elements get which features
   # css or xpath selector : OC Object name (without OC.)
   #
*/

OC.liveElementKey = {};

OC.liveElementKey.Element = {
    'TEXTAREA'               : 'FocusField', 
    'INPUT'                  : {'text'     :'FocusField',
                                'password' :'FocusField',
                                'file'     :'FocusField'}
}
OC.liveElementKey.Class = {
    "oc-js-autoSelect"       : "AutoSelect",
    "oc-js-expander"         : "Expander",
    "oc-js-fieldClear"       : "FieldClear",
    "oc-widget-multiSearch"  : "SearchLinks",
    'oc-dropdown-container'  : "DropDown",
    "oc-autoFocus"           : "AutoFocus",
    "oc-js-toggler"          : "Toggler",
    "oc-js-featurelet-undelete-warner" : "FeatureletUndeleteWarner",
    'oc-checkAll'            : "CheckAll",
    'oc-js-liveEdit'         : "LiveEdit",
    'oc-js-actionLink'       : "ActionLink",
    'oc-js-actionPost'       : "ActionLink",
    'oc-js-actionButton'     : "ActionButton",
    'oc-js-actionSelect'     : "ActionSelect",
    'oc-js-formConfirm'      : "FormConfirm",
    'oc-js-liveValidate'     : "LiveValidate",
    'oc-js-template'         : "Template",
    'oc-js-memberList'       : "MemberList",
    'oc-js-gmap'             : "GMap",
    "oc-js-closeable"        : "CloseButton",
    "oc-directEdit"          : "DirectEdit",
    "oc-js-unhide"           : "RevealElement",
    "oc-js-autosave"         : "CookieAutoSave",
    "oc-js-compactPassword"  : "CompactPassword",
    "oc-js-addWikiPage"      : "AddWikiPage"
};
OC.liveElementKey.Id = {
    "version_compare_form"   : "HistoryList",
    'oc-project-create'      : "ProjectCreateForm"
};
    
/* 
   # breathes life (aka js behaviors) into HTML elements.  call this on
   # load w/ no argument to breathe life to entire document.  When adding
   # new nodes to the dom, call breatheLife(newItem) to activate that
   # element and its children.
*/

OC.breatheLife = function(newNode, force) {

    OC.time('breatheLife');

    // force re-up?
    if (typeof force == "undefined") { force = false }
  
    // set scope
    if (!newNode) {
      targetNode = document.body;
    } else if (newNode.dom) {
      // accept HTML element or Ext Element
      targetNode = newNode.dom;
    } else {
      targetNode = newNode; 
    }
    
    // Build regexes out of our class list.  This allows
    // us to have one very quick lookup on elements to
    // prevent unnecessary processing.
    var classRegexString = '';
    for (var key in this.liveElementKey.Class) {
        if (classRegexString.length) {
            classRegexString += '|';
        }
        // Oh crap - and _ match end of word, we can't allow that
        classRegexString += '\\b' + key + '\\b(?![-_])';
    }
    var classRegex = new RegExp(classRegexString, 'g');

    // get an array of elements
    var elements = Ext.query('*', targetNode); 

    // loop through elements and match up against selectors
    for (var element = targetNode, i = -1, len=elements.length; i<len; element=elements[++i]) {
    
      // which constructors will we add to this element?
      var constructorNames = new Array();
    
      // check if element matches anything in the Elements list
      var tag_lookup = this.liveElementKey.Element[element.tagName];
      if (tag_lookup != undefined) {
        if (typeof tag_lookup == 'string') {
            constructorNames.push(tag_lookup);
        } else if (tag_lookup[element.type] != undefined) {
            constructorNames.push(tag_lookup[element.type]);
        }
      }
      
      // check if class matches anything in the Classes list
      // We only do full class processing if the regex registers
      // a hit against the class list.
      var matches = element.className.match (classRegex)
      if (matches) {
        for (var j=0; j<matches.length; j++) {
          constructorNames.push(this.liveElementKey.Class[matches[j]]); 
        }
      }
      
      // check if ID matches anything in the IDs list
      if (this.liveElementKey.Id[element.getAttribute('id')] != undefined) {
        constructorNames.push(this.liveElementKey.Id[element.getAttribute('id')]);
      }
      
      // foreach match, check to see if it exists
      // we break out the element retrieve so we only perform one per element.
      if (constructorNames.length > 0) {
        var extEl = Ext.get(element);
        for (var j=0; j<constructorNames.length; j++) {
          var constructorName = constructorNames[j];
          if (typeof OC.liveElements[extEl.id] == "undefined") { OC.liveElements[extEl.id] = {} };
          var constructor = OC[constructorName];
          
          if (force || typeof OC.liveElements[extEl.id][constructorName] == "undefined" ) {
            OC.liveElements[extEl.id][constructorName] = new constructor(extEl);
          }
        }
      }
      
    } // end for each element
    
    OC.timeEnd('breatheLife');

}; // breatheLife()

/*
  #------------------------------------------------------------------------
  # Utilities
  #------------------------------------------------------------------------
*/

// Debug Function.  Turn off for live code or IE
OC.debug = function(string) {
    /*
    args = ""
    for (var i = 0; i < arguments.length; ++i) {
      args += " " + arguments[i]
    }
    */
    return;
    if( typeof console != 'undefined' ) {
	     console.log(string);
    }
};

// Timer
OC.time = function(name) {
  if (typeof console != 'undefined') {
    //un-comment the line below to turn on timing
    //console.time(name);
  }
}
OC.timeEnd = function(name) {
  if (typeof console != 'undefined') {
    //un-comment the line below to turn on timing
    //console.timeEnd(name);
  }
}

// Send a message to the user
OC.psm = function(text, tone) {
    
    var container = Ext.get('oc-statusMessage-container');
    var message = Ext.get(Ext.query('.oc-statusMessage')[0]);

    if (!message) {
        message = Ext.get(document.createElement('div'));
        message.addClass('oc-message');
        container.dom.appendChild(message.dom);
    }

    /* tone: oc-message-error, oc-message-success, oc-message-warn */
    message.removeClass(new Array('oc-message-error', 'oc-message-success', 'oc-message-warn'));
    
    if (tone) {
        message.addClass('oc-message-' + tone);
    }
    
    message.update(text);
    message.show();
};

// Clean up the JSON response and eval it.
OC.CleanJSON = function(responseText) {
    // trim response text to avoid errors in IE
    OC.debug(responseText);
    var cleanedResponseText = responseText.replace(/[\r\n]/g, "");
    cleanedResponseText = cleanedResponseText.replace(/^\s*<html>.*?<body>/, "");
    cleanedResponseText = cleanedResponseText.replace(/<\/body>\s*<\/html>\s*$/, "")

    cleanedResponseText = cleanedResponseText.replace(/&lt;/g, "<");
    cleanedResponseText = cleanedResponseText.replace(/&gt;/g, ">");
    cleanedResponseText = cleanedResponseText.replace(/&amp;/g, "&");
    OC.debug(cleanedResponseText);
    
    var response = cleanedResponseText;
    try {
      var response = eval( "(" + cleanedResponseText + ")" );
    } catch( e ) {
      OC.debug(e);
      OC.debug("Couldn't parse the response.  Bad JSON? (below): ");
	  OC.debug(cleanedResponseText);
    }
    return response;
}

/* 
   #
   # Event wrapper to handle confirmation...
   #
*/

OC.Confirm = function(listener) {
    return function(e, el, o) {
        if (!el.className.match (/\boc-js-confirm\b/)) {
            return listener.call(this, e, el, o);
        }
        e && e.stopEvent();
        var message = Ext.get(el).child('span.oc-confirm')
        Ext.MessageBox.confirm('Confirm', message && message.dom.innerHTML || 'Are you sure?', function(response) {
            if ('yes' == response) {
                listener.call(this, e, el, o);
            }
        }, this);
        return false;
    }
}

// A function to install handle a submit blocker for a text field for handling
// the enter key.
OC.SubmitBlocker = function(form, field, action) {

    if (!form) {
        return;
    }

    field.addListener({scope: this,
        'focus': function() {
            form.addListener({scope: this,
                'submit': action,
                stopEvent: true});
        },
        'blur': function() {
            form.removeListener('submit', action);
        }
    });
}

/*
  #
  # DOM Utilities
  #
*/
OC.Dom = {};

// remove an item from the dom
OC.Dom.removeItem = function(id) {
    var extEl = Ext.get(id);
    if (!extEl) {
      OC.debug("Could not find an element #" + id);
      return;
    }
    extEl.fadeOut({remove: true, useDisplay: true});
    OC.debug(OC.liveElements[extEl.id]);
    delete OC.liveElements[extEl.id];
    OC.debug(OC.liveElements[extEl.id]);
    
    // to do: send user message w/ undo link
};
    
/*
  #------------------------------------------------------------------------
  # Load Em up
  #------------------------------------------------------------------------
*/

Ext.onReady(function() {

  /* Short and Sweet */
  OC.breatheLife();

});

/*
  #------------------------------------------------------------------------
  # Callbacks - Static object with ajax callbacks
  #------------------------------------------------------------------------
*/
OC.Callbacks = {};

OC.Callbacks.afterAjaxSuccess = function(o) { 
    OC.debug('OC.Callbacks.afterAjaxSuccess');
    
    try {  
      this.indicator.hide();  
    } catch(err) { 
      OC.debug(err); 
    }
    try {  
      if (this.button.dom.innerHTML == "Please wait...") {
          OC.debug("link innerhtml: " + this.button.dom.innerHTML);
          OC.debug("link origValue: " + this.origButtonValue);
          this.button.dom.innerHTML = this.origButtonValue;
      }
      if (this.button.dom.value == "Please wait...") {
          OC.debug("button value:" + this.button.dom.value);
          OC.debug("button origvalue: " + this.origButtonValue);
        this.button.dom.value = this.origButtonValue;
      }
      if (this.button.dom.disabled) {
        this.button.dom.disabled = false;  
      }
    } catch(err) {
      OC.debug("couldn't restore button value");
       OC.debug(err); 
    }
    
    Ext.select('form').each(function(el) {
	    el.dom.target = "";
	   });
    OC.debug('o: ' + o);
    
    var response = OC.CleanJSON(o.responseText);
    
    if( response instanceof Array ) {
	// for backcompatibility with existing code. consider
	// deprecated.  we will translate the array into an object
	// with "delete" actions for each elId, since that's the only
	// case where we used to expect an array.
	var newResponse = {};
	for( var iter = 0; iter < response.length; ++iter ) {
	    newResponse[response[iter]] = {'action': 'delete'};
	}
	response = newResponse;
    }
    
  for( elId in response ) {
	var command = response[elId];
	var action = command.action;
	
	switch( action ) {
	case "error":
            var target = Ext.get(elId);
            target.frame();
            break;

	case "delete":
	    OC.debug("DELETE on " + elId);
	    OC.Dom.removeItem(elId);
	    break;
	    
	case "replace":
	    var html, effects;	    	    
            effects = command.effects;
            html = command.html;

	    OC.debug("REPLACE " + elId + " with " + html + " using effect " + effects);
	    
	    html = Ext.util.Format.trim(html);
	    var target = Ext.get(elId);
            if (!target) {
                // This particular target hasn't been found
                break;
            }
	    var newNode = Ext.DomHelper.insertHtml('beforeBegin', target.dom, html);
	    target.remove();

	    if( effects == "highlight") {
                Ext.get(newNode).highlight();
	    } else if( effects == "fadein" ) {
                Ext.get(newNode).fadeIn();
	    }
	    
	    OC.breatheLife(newNode, true);
	    OC.debug("done breathing");
	    
	    break;

        case "replace-by-query":
            // elId is a misnomer in this case :P
            var html, effects;
            effects = command.effects;
            html = command.html;

            OC.debug("REPLACE BY QUERY " + elId + " with " + html + " using effect " + effects);

            html = Ext.util.Format.trim(html);
            var target_array = Ext.query(elId);
            if (target_array.length == 0) {
                break;
            }

            for (var i=0; i<target_array.length; i++) {
                var oldNode = target_array[i];
                var newNode = Ext.DomHelper.insertHtml('beforeBegin', oldNode, html);
                oldNode.parentNode.removeChild(oldNode);

                if ( effects == "highlight") {
                    Ext.get(newNode).highlight();
                } else if ( effects == "fadein" ) {
                    Ext.get(newNode).fadeIn();
                }

                OC.breatheLife(newNode, true);
                OC.debug("done breathing");

            }
            break;

	case "copy":
	    var html = command.html;
	    var effects = command.effects;
	    
	    html = Ext.util.Format.trim(html);
	    var target = Ext.get(elId);
	    if(! target ) break;
	    
	    Ext.DomHelper.overwrite(target.dom, html);
	    var newNode = target;
	    if( effects == "highlight" ) {
		Ext.get(newNode).highlight();
	    }
	    //OC.breatheLife();
	    break;
	    
	case "append": // fill me in
	    var html = command.html;
	    var effects = command.effects;
	    
	    html = Ext.util.Format.trim(html);
	    var target = Ext.get(elId);
	    
	    var newNode = Ext.DomHelper.insertHtml("beforeend", target.dom, html);
	    if( effects == "highlight" ) {
		Ext.get(newNode).highlight();
	    }
	    OC.breatheLife();
	    break;
	    
	case "prepend": // fill me in
	    
	default:
	    OC.debug('_afterSuccess, task: default');
	    break;
	} // end switch on action
    } // end for each element
}; // end OC.Callbacks.afterAjaxSuccess()

OC.Callbacks.afterAjaxFailure = function(o) {
    OC.debug('OC.Callbacks.afterAjaxFailure');
    OC.debug(o.responseText);
};

/*
  #------------------------------------------------------------------------
  # Classes - will become liveElement objects
  #------------------------------------------------------------------------
*/

/* 
   #
   # Form submission wrapper to provide non browser modal confirm
   #
*/

OC.FormConfirm = function(extEl) {
    var form = extEl;

    if (!form || !form.dom || form.dom.tagName != 'FORM') {
        OC.debug('FormConfirm: invalid form reference');
        return;
    }

    // Add click handlers to the submit buttons to store which
    // button triggers the form.
    var buttons = Ext.query('input[type=submit], button[type=submit]', form.dom);
    for (var index = 0; index < buttons.length; ++index) {
        Ext.get(buttons[index]).on('click', function(e, el, o) { form._confirm_trigger = el.dom || el;}, this);
    }

    // Set up the first submit button as the default handler, as browsers do.
    if (buttons[0]) {
        form._confirm_trigger = buttons[0];
    }

    form.on('submit', function(e, el, o) {
        if (form.confirmed) {
            return true;
        }
        e.stopEvent();
        var message = Ext.get(el).child('span.oc-confirm')
        Ext.MessageBox.confirm('Confirm', message && message.dom.innerHTML || 'Are you sure?', function(response) {
            if ('yes' == response) {
                form.confirmed = true;
                form._confirm_trigger.click();
            }
            }, this);
        return false;
        }, this);
}

/* 
   #
   # Action Links submit via XHR rather than plain requests.  
   # With oc-js-actionPost, the method is POST; else it is GET
   #
*/
OC.ActionLink = function(extEl) {
    // get refs
    var link = extEl;
    this.button = link; /* for ajax callback */
    this.origButtonValue = this.button.dom.innerHTML; /* for ajax callback */
    
    if (!link) {
	     OC.debug("ActionLink: Could not get refs");
    } 

    function _doAction(e, el, o) {
    	e.stopEvent();
    	
        if (link.hasClass('oc-js-actionPost')) {
            var method = "POST";
        } else {
            var method = "GET";
        }

    	// get action/href & split action from params
    	var action = el.href.split("?")[0];
    	var requestData = el.href.split("?")[1] + '&mode=async';
    	OC.debug("request data is " + requestData);
    	
    	this.button.dom.innerHTML = "Please wait..."; 
    	
    	// make connection
        if (method == "GET") {
        	var cObj = YAHOO.util.Connect.asyncRequest("GET", action + '?' + requestData, {
        		success: OC.Callbacks.afterAjaxSuccess, 
        		failure: OC.Callbacks.afterAjaxFailure,
        		scope: this 
        	    });
        } else if (method == "POST") {
        	var cObj = YAHOO.util.Connect.asyncRequest("POST", action, {
        		success: OC.Callbacks.afterAjaxSuccess, 
        		failure: OC.Callbacks.afterAjaxFailure,
        		scope: this 
        	    }, requestData);
        }
    }

    link.on('click', OC.Confirm(_doAction), this);
    
    // pass back element to OC.LiveElements
    return this;
};

/* 
   #
   # Action Select
   #
*/
OC.ActionSelect = function(extEl) {
    // get refs
    var container = extEl;
    var select = Ext.get(Ext.query('select',container.dom)[0]);
    var submit = Ext.get(Ext.query('input[type=submit], button[type=submit]', container.dom)[0]);
    var hideFormLink = Ext.get(document.body);
    var form = select.up('form');
    var liveEdit = select.up('.oc-js-liveEdit');
    
    // get a reference to the liveElement that this is part of.
    if (liveEdit) { 
      var liveEdit = OC.liveElements[liveEdit.id]['LiveEdit'];
    }
    
    
    //check refs
    if (!select) {
      OC.debug("ActionSelect: Couldn't get refs");
    return;
    } 
    
    //settings
    var action = form.dom.action;
    var orig_task = submit.dom.name;
    var task = submit.dom.name;
    submit.setVisibilityMode(Ext.Element.DISPLAY);
    submit.hide();

    if (task.slice(0,5) != 'task|') {
        task = 'task|' + task;
    }
    var taskValue = submit.dom.value;
    
    function _doAction(e, el, o) {
        // if the actionSelectTask element doesn't begin w/ 'task|', we add it
        submit.dom.name = task;
        OC.debug("ActionSelect: submit.dom.name: " + submit.dom.name);
        YAHOO.util.Event.stopEvent(e);
        YAHOO.util.Connect.setForm(form.dom);
        var cObj = YAHOO.util.Connect.asyncRequest("POST", action, {
          success: OC.Callbacks.afterAjaxSuccess,
          failure: OC.Callbacks.afterAjaxFailure,
          scope: this
	    }, "mode=async&" + task + "=" + taskValue);
        // restore original task element name
        submit.dom.name = orig_task;
    }
    select.on('change', OC.Confirm(_doAction), this);
    
    function _hideParentForm(e, el) {
      if (liveEdit.isOpen()) {
        liveEdit.hideForm(e, el);
      }
    }
    if (hideFormLink) {
      hideFormLink.on('click', _hideParentForm, this);
    }
    
    
    // pass back element to OC.LiveElements
    return this;
};

/* 
   #
   # Action Buttons: causes a submit button to submit a XHR, rather
   # than a plain request.
*/
OC.ActionButton = function(extEl) {
    // get refs
    this.button = extEl;
    var form = this.button.up('form');
    var name = this.button.dom.name.replace('task|', "");

    // In order to have good performance, actionButtons
    // must be tagged if they actually have an indicator.  This
    // prevents really expensive whole page searches otherwise.
    if (extEl.hasClass('oc-has-indicator')) {
      this.indicator = Ext.get('indicator|' + name);
    }
        
    // check refs
    if (!this.button || !form) {
      OC.debug("ActionButton: Couldn't get refs");
      return;
        } 
    
    // settings
    var action = form.dom.action;
    var task = this.button.dom.name;
    var taskValue = this.button.dom.value;
    var isUpload = false;
    this.origButtonValue = this.button.dom.value;
    if (this.indicator) {
      this.indicator.setVisibilityMode(Ext.Element.DISPLAY);
      this.indicator.hide();
    }
    
    if (form.dom.enctype == "multipart/form-data") {
      OC.debug("is upload ...");
      isUpload = true;
    }
  
    function _actionButtonClick(e, el, o) {
    
     try { this.indicator.show(); } catch(err) { OC.debug(err); }
     
     try { this.button.dom.value = "Please wait..."; this.button.dom.disabled = true; } catch(err) { OC.debug(err); }
	   
	 OC.debug("_actionButtonClick");
    
     // Why is the event stopped ???
     YAHOO.util.Event.stopEvent(e);
      if (isUpload) {
          YAHOO.util.Connect.setForm(form.dom, true);
      } else {
          YAHOO.util.Connect.setForm(form.dom);
      }
      OC.debug("...........task is " + task);
     var cObj = YAHOO.util.Connect.asyncRequest("POST", action, {
	     success: OC.Callbacks.afterAjaxSuccess,
	     upload: OC.Callbacks.afterAjaxSuccess,
	     failure: OC.Callbacks.afterAjaxFailure,
	     scope: this
	 }, "mode=async&" + task + "=" + taskValue);

     if( task == "task|upload-attachment" ) {
     
       // can't cross-browser clear a file input.  Recreate it and delete the original
       var oldInput = Ext.get("attachmentFile");
       var inputHTML = oldInput.dom.parentNode.innerHTML;       
       var newInput = Ext.DomHelper.insertHtml('beforeBegin', oldInput.dom, inputHTML);
       oldInput.remove();
       
       // clear title field
       Ext.get("attachmentTitle").dom.value = "";

     }

    }

    // This is a submit button to allow this form to work without javascript.  Unfortunately,
    // having a submit button with a click handler breaks the enter button functionality.
    // Since we know javascript is enabled (We're running, right?), we will turn this into
    // a regular button.
    this.button.dom.type = 'button';

    this.button.on('click', OC.Confirm(_actionButtonClick), this);
    
    // pass back element to OC.LiveElements
    return this;
};

/* 
   #
   # CheckAll
   #
*/
OC.CheckAll = function(extEl) {
    // get refs
    var checkAll = extEl;
    var form = checkAll.up('form');  
    OC.debug(checkAll);
    OC.debug(form);
    var allBoxes = Ext.select(Ext.query('input[type=checkbox]:not(.oc-js-checkAll-never)', form.dom));
    
    OC.debug(allBoxes);
    // check refs
    if (!checkAll || !form || !allBoxes) {
	OC.debug("CheckAll: Couldn't get refs");
    } 
    
    function _toggleCheckBoxes(e, el, o) {
	OC.debug('_checkAllClick');
	if (el.checked) {
	    allBoxes.set({checked: true}, false);
	} else {
	    allBoxes.set({checked: false}, false);
	}
    }
    
    checkAll.on('click', _toggleCheckBoxes, this); 
    
    // pass back element to OC.LiveElements
    return this;
};

/*
  #
  # Live Validate
  #
*/
OC.LiveValidate = function(extEl) {
    // get refs
    var field = extEl;
    var form = field.up('form');

    function _validateField(e, el, o) {
      
        var request = "";
        for (var i=0; i<form.dom.elements.length; i++) {
            var input = form.dom.elements[i];
            if (input.value && input.type != 'submit') {
            var value = form.dom.elements[i].value
            var encoded = escape(value);
            encoded = encoded.replace("+", "%2B");
            request += form.dom.elements[i].name + "=" + encoded + "&";
            }
        }      
        
        // send ajax request
        var action = form.dom.action;
    
        var cObj = YAHOO.util.Connect.asyncRequest("POST", action, {
            success: OC.Callbacks.afterAjaxSuccess, 
            failure: OC.Callbacks.afterAjaxFailure, 
            scope: this 
            }, request + "task|validate=validate&mode=async");    
    }
    field.on('blur', _validateField, this);
    
    function _afterValidateFailure(o) {
    
    }
    
    // pass back element to OC.LiveElements
    return this;
    
};

/* 
   #
   # Auto Focus
   # 
*/
OC.AutoFocus = function(extEl) {
    // get refs
    extEl.dom.focus();
    
    // pass back element to OC.LiveElements
    return this;
};

/*
  #
  # Focus Field
  #
*/
OC.FocusField = function(extEl) {
    // get refs
    var field = extEl;
    
    // check refs
    if (!field) {
	OC.debug("FocusField: Could not get refs");
	return;
    }
    
    function _highlightField(e, el, o) {
	var container = Ext.get(el).up('.oc-fieldBlock'); 
	if (container) {
	    container.addClass('oc-fieldBlock-focused');
	}
	Ext.get(el).addClass('oc-fieldBlock-focused');
    }
    function _unHighlightField (e, el, o) {
	var container = Ext.get(el).up('.oc-fieldBlock'); 
	if (container) {
	    container.removeClass('oc-fieldBlock-focused');
	}
	Ext.get(el).removeClass('oc-fieldBlock-focused');
    }
    field.on('focus', _highlightField, this);
    field.on('blur', _unHighlightField, this);
    
    // pass back element to OC.LiveElements
    return this;
};

/* 
   #
   # OC Upload Form
   # FIXME: Re-do this so it works as a LiveForm
   # 
*/
OC.UploadForm = function(extEl) {
    //get references
    var form = extEl;
    var targetId = Ext.get(Ext.query('input[name=oc-target]',form.dom)[0]).dom.value;
    var target = Ext.get(targetId);
    var indicator = Ext.get(Ext.query('.oc-indicator',form.dom)[0]);
    var submit = Ext.get(Ext.query('input[type=submit], button[type=submit]',form.dom)[0])
    
    //check refs
    if (!form || !target || !indicator || !submit) {
        OC.debug('UploadForm: element missing');
        return;
    }
    
    //vars & settings
    var isUpload = false;
    if (form.dom.enctype)
        isUpload = true;
    OC.debug("Enctype: " + form.dom.enctype);
    indicator.setVisibilityMode(Ext.Element.DISPLAY);
    indicator.hide();
    
    // loading
    function _startLoading() {
        indicator.show();
        submit.dom.disabled = true;
        submit.originalValue = submit.dom.value;
        submit.dom.value = "Please wait..."
	    }
    function _stopLoading() {
        indicator.hide();
        submit.dom.disabled = false;
        submit.dom.value = submit.originalValue;
        form.dom.reset();
    }
    
    //ajax request
    function _formSubmit(e, el, o) {
        YAHOO.util.Event.stopEvent(e);
        
        if (isUpload)
            YAHOO.util.Connect.setForm(el, true);
        else 
            YAHOO.util.Connect.setForm(el);
	
        var callback = {
	    success: _afterSuccess,
	    upload: _afterUpload,
	    failure: _afterFailure,
	    scope: this
        }
	OC.debug("Action: " + form.dom.action);
        var cObj = YAHOO.util.Connect.asyncRequest("POST", form.dom.action, callback);
        _startLoading(); 
	
    }
    form.on('submit', OC.Confirm(_formSubmit), this);
    
    // after request
    function _afterUpload(o) {
        _stopLoading(); 
        
        // response object will be { status : success }  or { status : failure }
        var response = eval( '(' + o.responseText + ')' );
        
        switch (response.status) {
	case "success" :
            _afterUploadSuccess(response);
	    break;
	case "failure" :
            _afterUploadFailure(response);
	    break;
	default:
            OC.debug('_afterUpload response.status: default');
        } 
    }
    function _afterUploadSuccess(response) {
	OC.debug('_afterUploadSuccess');
	
	//2nd ajax request
	var cObj = YAHOO.util.Connect.asyncRequest("GET", response.updateURL, { 
		success: function(o) {
		    
		    // insert new - DomHelper.insertHtml converts string to DOM nodes
		    o.responseText = Ext.util.Format.trim(o.responseText);
		    var newNode = Ext.DomHelper.insertHtml('beforeEnd', target.dom, o.responseText);
		    Ext.get(newNode).highlight("ffffcc", { endColor: "eeeeee"});
		    
		    //re-up behaviors on new element
		    OC.breatheLife(newNode);
		}, 
		failure: function(o) {
		    OC.debug('upload failed');
		},
		scope: this 
	    });
	
      
    }
    
    function _afterFailure(o) {
        OC.debug('_afterFailure RESPONSE BELOW:\n\n');
        for (prop in o) {
	    OC.debug(prop + ":");
	    OC.debug(o["" + prop + ""]);
        }
    }
    function _afterSuccess(o) {
        OC.debug('_afterSuccess RESPONSE BELOW:\n\n'); 
        for (prop in o) {
	    OC.debug(prop + ":");
	    OC.debug(o["" + prop + ""]);
        }
    }
    
    return this;
};

/*
  #
  # DropDown
  #
*/
OC.DropDown  = function(extEl) {
    // get refs
    var container = extEl;
    var topLink = Ext.get(Ext.query("#" + container.id + " > a")[0]);
    var submenu = Ext.get(Ext.query('ul', container.dom)[0]);
    var unclickArea = Ext.get(document.body);
    
    // check refs
    if (!container || !submenu || !unclickArea) {
      OC.debug("TopNav: couldn't get refs");
      return;
        } 
    
    // settings
    var overrideHide = false;
    
    function _toggleMenu(e) {
      if (submenu.isVisible()) {
        _hideMenu();          
      } else {
        _showMenu();
      }
    }
    
    function _showMenu() {
      _hideMenu();
      submenu.show();
      overrideHide = true;
      container.addClass('oc-selected');
    }
    
    function _hideMenu() {
      if (!overrideHide) {
          submenu.hide();
          container.removeClass('oc-selected');
      }
      overrideHide = false;
    }
    
    function _toggleMenuPreview() {
      if (container.hasClass('oc-hover')) {
          container.removeClass('oc-hover');
      } else {
          container.addClass('oc-hover');
      }
    } 
  
    container.on('mouseover', _toggleMenuPreview, this);
    container.on('mouseout', _toggleMenuPreview, this);
    container.on('click', _toggleMenu, this);
    
    if (topLink) {
      topLink.on('click', function(e, el) {
        YAHOO.util.Event.preventDefault(e);
      });
    }
    
    unclickArea.on('click', _hideMenu, this );
    
    // pass back element to OC.LiveElements
    return this;
};

/* 
   #
   #  Project Create Form
   #
*/
OC.ProjectCreateForm = function(extEl) {
    // get refs
    var form = extEl;
    var nameField = Ext.get(Ext.query('input#project_title')[0], form.dom);
    var urlField = Ext.get(Ext.query('input#projid')[0], form.dom);
    
    // check refs
    if (!form || !nameField || !urlField) {
	     OC.debug("ProjectCreateForm: couldn't get refs");
         return;
    }
    
    // settings & properties
    /* has the user manually overridden our suggested url? */
    var customUrl = false;
    
    // suggested URL
    var suggestedUrl = "";
    
    function _urlize(e, el, o) {
      if (!customUrl) {
          suggestedUrl = Ext.util.Format.trim(el.value).toLowerCase().replace(/[^a-zA-Z0-9\s_-]/gi, "").replace(/\s+/g, "-");
          urlField.dom.value = suggestedUrl;
      } else {
          OC.debug('custom URL: will not suggest'); 
      }
    }
    nameField.on('keyup', _urlize, this);
    urlField.on('keyup', _urlize, this);
    
    function _checkForCustomUrl(e, el, o) {
      if (el.value != suggestedUrl) {
          customUrl = true;
          OC.debug('custom url')
        }
      OC.debug('customUrl: ' + customUrl)
    }
    urlField.on('keyup', _checkForCustomUrl, this);
    
    /* TO DO: Validate project url via Ajax
       #  title field: onblur
       #  url field: onkeyup
       #
    */  
    
    // pass back element to OC.LiveElements
    return this;
    
}; // end OC.ProjectCreateForm()

/* 
   #
   # Live Edit
   # Show/hide editable version of a value.  
   #
*/
OC.LiveEdit = function(extEl) {
    
    // get references
    var container = extEl;
    var value = Ext.get(Ext.query('.oc-js-liveEdit-value', container.dom)[0]); 
    var editForm = Ext.get(Ext.query('.oc-js-liveEdit-editForm', container.dom)[0]);  
      
    var showFormLink = Ext.select(Ext.query('.oc-js-liveEdit_showForm', container.dom));
    var hoverShowFormLink = Ext.select(Ext.query('.oc-js-liveEdit_hoverShowForm', container.dom));
    var hideFormLink = Ext.select(Ext.query('.oc-js-liveEdit_hideForm', container.dom));
    //if (hideFormLink.elements.length == 0) hideFormLink = Ext.get(document.body);
        
    if (!value || !editForm) {
        OC.debug("liveEdit: Couldn't get element refs");
        return;
    }
    
    // settings
    value.setVisibilityMode(Ext.Element.DISPLAY);
    editForm.setVisibilityMode(Ext.Element.DISPLAY);
    editForm.hide();
    var hideThisForm = false;
    var directEdit = false;
    if (value.hasClass('oc-directEdit')) {
      directEdit = true;
    }
    
    // make sure a click on the container doesn't close the form.  stop the event bubbling.
    container.on('click', _stopEvent, this)
    function _stopEvent(e) {
      OC.debug("stopEvent");
      e.stopPropagation();
    }

    function _toggleForm(e) {
        if (editForm.isVisible()) {
          _hideForm(e);
        } else {
          _showForm(e);
        }
    }
    
    function _hideForm(e, el) {
        if (hideThisForm) {
          if (Ext.get(el)) {
            if (Ext.get(el).hasClass('oc-js-liveEdit_hideForm')) {
              e.preventDefault();
            }
          }
          value.show();
          editForm.hide();
        }
        hideThisForm = false;
    }

    function _showForm(e) {
        e.stopEvent();
        value.hide();
        editForm.show();
        hideThisForm = true;
        var form = Ext.get(Ext.query('input[type=text]', editForm.dom)[0]) || Ext.get(Ext.query('select', editForm.dom)[0]);
        if (form) { form.focus(); }
    }
    
    if (showFormLink) {
      showFormLink.on('click', _showForm, this, {stopPropagation: true});
    }
    if (hoverShowFormLink) { 
      hoverShowFormLink.on('click', _toggleForm, this);
    }
    if (hideFormLink) {
        hideFormLink.on('click', _hideForm, this);
    }
    
    if (directEdit) {
      // liveEdit value behaviors
      function _valueMouseover(e, el, o) {
          value.addClass('oc-directEdit-hover');
      }
      value.on('mouseover', _valueMouseover, this);
      
      function _valueMouseout(e, el, o) {
          value.removeClass('oc-directEdit-hover');
      }
      value.on('mouseout', _valueMouseout, this);
    }
    
    
    // Public properties & methods
    this.toggleForm = _toggleForm;
    this.hideForm = _hideForm;
    this.isOpen = function() {
      if (!value.isVisible() && editForm.isVisible()) {
        return true;
      } else {
        return false;
      }
    }
    
    return this;
};

OC.DirectEdit = function(extEl) {
    

}

/* 
   #
   # Search Links
   #
*/
OC.SearchLinks = function(extEl) {
    // get references
    var form = extEl.dom.getElementsByTagName('form')[0];
    var links = Ext.select(Ext.query('a' ,form));
    var text = Ext.get(Ext.query('input[type=text]', form)[0]);
    
    // check refs
    if (!form || !links || !text) {
	OC.debug("SearchLinks: could not get element refs");
    } 
    
    // find current value
    var url = window.location.toString();
    var urlBase = url.split('?')[0];
    var querystring = url.split('?')[1] || "";
    if (querystring) {  
	var param_groups = querystring.split('&');
	var params = {}
	for (var i=0; i<param_groups.length; i++) {
	    var key = param_groups[i].split("=")[0];
	    var value = param_groups[i].split("=")[1];
	    params[key] = value;
	}
    }
    
    function _linksMouseover(e, el, o) {
	var el_urlBase = el.href.split('?')[0];
	
	if (text.dom.value) {
	    // get form value
	    var newQuery = YAHOO.util.Connect.setForm(form);
	    // replace link 
	    el.href = el_urlBase + "?" + newQuery;    
	} else {
	    el.href = el_urlBase + "?" + querystring;
	}
	
    }
    links.on('mouseover', _linksMouseover, this);
    
    // pass back element to OC.LiveElements
    return this;
    
}; // end OC.SearchLinks();

/* 
   #
   # Close Buttons
   #
*/
OC.CloseButton = function(extEl) {
    // get references.  No ID naming scheme.  just use parent node.
    var container = extEl;
    var close_button = Ext.get(document.createElement('a'));
    close_button.dom.innerHTML = '&times;';
    close_button.dom.href = '#';
    close_button.dom.title = 'close';
    close_button.addClass('oc-closeButton');
    container.dom.appendChild(close_button.dom);

    // XXX do only psms use this?
    container.fadeIn();
    container.setVisibilityMode(Ext.Element.DISPLAY);
    
    //behaviors
    function _closeButtonClick(e, el, o) {
        container.fadeOut({});
        YAHOO.util.Event.stopEvent(e);
    }
    close_button.on('click', _closeButtonClick, this);

    return this;
};

/*
  #
  # Warn Popups
  #  -- THIS IS DUMB AND SHOULD BE LOOKED OVER BY NICK TO MAKE BETTER
*/
OC.FeatureletUndeleteWarner = function(extEl) {

  //get refs
  var container = extEl;
  var checkbox = Ext.get(container.dom.getElementsByTagName('input')[0]);
  var warning = Ext.get(Ext.query('.oc-warning', container.dom)[0]);

  
  //check refs
  if (!checkbox || !container || !warning) {
    return;
  } 

  // we only want to display the error message
  // if the element wasn't already selected by default
  // in other words, only display the warning if the user is taking away
  // the featurelet, not if they added it and took it away
  if (checkbox.dom.checked) {
    checkbox.on('click', function(e, el) { 
      if (!el.checked) {
        warning.show();
      } else {
        warning.hide();
      }
    });
  }
};

/* 
   #
   # Select Box Auto Links
   #
*/
OC.AutoSelect = function(extEl) {
    // get references.  No ID naming scheme yet.  just use parent node.
    var select = extEl;
    var form = select.dom.parentNode;
    var submit = Ext.get(Ext.query('input[type=submit], button[type=submit]', form)[0]);
    
    
    if (!select || !submit || !form) {
	OC.debug('AutoSelect: couldnt get refs;');
	return;
    } else {
	OC.debug("AutoSelect: got refs");
    }
    
    //submit 
    submit.setVisibilityMode(Ext.Element.DISPLAY);
    submit.hide();
    
    //behaviors
    function _selectChange(e, el, o) {
        form.submit();
    } 
    select.on('change', OC.Confirm(_selectChange), this);
    
    return this;
};

/* 
   #
   # Expanders
   #
*/
OC.Expander = function(extEl) {
    // get references.
    var container = extEl;
    var expanderLink = Ext.select(Ext.query(".oc-js-expander_open", container.dom));
    var content = Ext.get(Ext.query(".oc-js-expander-content",  container.dom)[0]);
    var closeLink = Ext.select(Ext.query(".oc-js-expander_close", container.dom));
    
    // check to make sure we have everything
    if(!container || !expanderLink || !content) {
	     OC.debug('OC.Expander: couldn\'t get element references');
        return;
    }
    
    // settings
    content.setVisibilityMode(Ext.Element.DISPLAY);	
    
    function _expand() {
	   content.slideIn('t',{duration: .1});
	   container.addClass('oc-expander-open');
	   expanderLink.addClass('oc-expanderLink-open');
	   if (closeLink) closeLink.show();
    }
    function _contract() {
    content.slideOut('t',{duration: .1});
    container.removeClass('oc-expander-open');
    expanderLink.removeClass('oc-expanderLink-open');
    if (closeLink) closeLink.hide();
    }
    
    //link
    function _linkClick(e, el, o) {
        if (!content.isVisible()) {
            _expand();
        } else {
            _contract();
        } 
        YAHOO.util.Event.stopEvent(e);
    }
    expanderLink.on('click', _linkClick, this);
    if (closeLink) closeLink.on('click', _linkClick, this);
        
    // init (when breatheLife is called)
    if (!container.hasClass('oc-expander-open')) {
	_contract();
    }
    
    return this;
};


/*
  #
  # Clear all inputs of the form this element appears in
  #
*/
OC.FieldClear = function(extEl) {
    // get references
    var link = extEl;
    var fieldname = link.dom.getAttribute("oc:target");
    var field = document.getElementById(fieldname);
    
    // check references
    if (!link || !field) {
        OC.debug("OC.FieldClear could not get references");
        return;
    }

    function _clearField() {
        OC.debug("in clearField");
        field.value = "";
    }

    link.on("click", _clearField, this, {preventDefault: true});
};


/*
  #
  # History List
  #
*/
OC.HistoryList = function(extEl) {
    // setup references
    var form = extEl;
    var compareButtons = Ext.select('form#' + form.dom.id + ' input[type=submit], form#' + form.dom.id + ' button[type=submit]');
    var versions  = Ext.get(Ext.select('form#' + form.dom.id + ' li'));
    var checkboxes = Ext.get(Ext.select('form#' + form.dom.id + ' input[type=checkbox]'));
    var userMessage = Ext.get(Ext.query('.oc-message', form.dom)[0]);
    
    //check references
    if (!form || !compareButtons || !versions || !userMessage) {
        OC.debug("OC.historyList couldn't get all element references.");   
        return;
    }
    
    //validator
    userMessage.setVisibilityMode(Ext.Element.DISPLAY);
    userMessage.hide();
    
    //compare buttons
    var enableCompareButtons = true;
    function _compareButtonClick(e, el, o) {
	if (!enableCompareButtons) {
	    YAHOO.util.Event.stopEvent(e);
	    userMessage.update("Please select exactly two versions to compare.");
	    userMessage.addClass('oc-message-error');
	    userMessage.show();
	}
    }
    compareButtons.on('click', _compareButtonClick, this);
    
    //checkboxes
    function _clearCheckboxes() {
	checkboxes.each(function(extEl) {
		extEl.dom.checked = false;
		Ext.get(extEl.dom.parentNode).removeClass('oc-selected');
	    });
    }
    function _countChecked() {
	//count # checked
	var numChecked = 0;
	checkboxes.each(function(extEl) {
		if (extEl.dom.checked) {
		    numChecked++;
		}
	    });
	OC.debug(numChecked);
	return numChecked;
    }
    function _setList() {
	//if exactly 2, enable compare buttons
	if (_countChecked() == 2) {
	    enableCompareButtons = true;
	    userMessage.fadeOut();
	} else {
	    enableCompareButtons = false;   
	}
	
	checkboxes.each(function(extEl) {
		//highlight this checkbox's parent
		if (extEl.dom.checked) 
		    Ext.get(extEl.dom.parentNode).addClass('oc-selected');
		else
		    Ext.get(extEl.dom.parentNode).removeClass('oc-selected');
	    }, this);
    }
    
    function _checkboxClick(e, el, o) {
	var checkMe = false;
	if (el.checked) {
	    checkMe = true;
	}
	//if more than 2, clear all and check currentStyle
	if (_countChecked() > 2) {
	    _clearCheckboxes();
	} 
	if (checkMe) {
	    // re-check since checklist clears it
	    el.checked = true;
	}
	_setList();
    }
    checkboxes.on('click', _checkboxClick, this)
    
    //Init
    _setList();
    
    OC.debug(form.dom.elements);
    
    return this;
};

OC.Toggler = function(extEl) {
    var checkbox = extEl;
    var label = Ext.get(checkbox.dom.id.replace('toggler', 'togglee'));
    var radio = Ext.get(label.dom.getElementsByTagName('input')[0]);
    var wiki = Ext.get(Ext.get('oc-js-togglee-wiki').dom.getElementsByTagName('input')[0]);
    // check references
    if (!checkbox || !radio || !wiki || !label) {
        OC.debug('Error getting references for toggler');
        return false;
    }
    _handle_toggle();
    function _handle_toggle() {
        if (checkbox.dom.checked) {
            radio.dom.disabled = false;
            label.removeClass('oc-disabled');
        } else {
            radio.dom.disabled = true;
            label.addClass('oc-disabled');
            if (radio.dom.checked) {
                wiki.dom.checked = true;
            }
        }
    }
    checkbox.on('click', _handle_toggle, this);
};

/* 
   #
   # Content Template
   #
*/
OC.Template = function(extEl) {
    // get refs
    anchor = extEl;
    
    if (!anchor) {
         OC.debug("Template: Could not find template anchor");
    } 

    template = anchor.id.split('oc-template-')[1];

    if (undefined == template) {
        OC.debug("Template: No template referenced by id");
    }

    var templateHtml = YAHOO.util.Connect.asyncRequest("GET", '++resource++' + template, {
        success: OC.Callbacks.afterAjaxSuccess, 
        failure: OC.Callbacks.afterAjaxFailure,
        scope: this 
    });
};

/* 
   #
   # GMap Div
   #
*/
OC.GMap = function(extEl) {
    // Verify JS support
    if ((typeof(GBrowserIsCompatible) == 'undefined' || (!GBrowserIsCompatible()))){
        OC.debug("GMap: Google Map API not loaded or unsupported browser");
        if (extEl) {
            extEl.dom.parentNode.removeChild(extEl.dom);
        }
        return;
    }

    // Get required elements
    var mapdiv = extEl;
    
    if (!mapdiv) {
        OC.debug("GMap: Could not find map div");
        return;
    } 

    // Lat/Lon of TOPP (used as a default map starting location)
    var default_point = new GLatLng(40.738067, -74.006952);

    // Look for an existing latitude/longitude pair.
    var input_latitude = Ext.get(mapdiv.id + '-latitude');
    var input_longitude = Ext.get(mapdiv.id + '-longitude');

    // If we have only one coordinate, we can't properly proceed
    if ((input_latitude && !input_longitude) || (input_longitude && !input_latitude)) {
        OC.debug("GMap: Missing " + (input_latitude ? 'longitude' : 'latitude') + ' coordinate');
        return;
    }

    // If we have a form, we need to hook up our UI.
    var control_button = Ext.get('oc-map-update-button');
    var is_static_map = false;
    if( !control_button ) {
        is_static_map = true;
    } else {

        // If the control button has a parent form, we'll put in a submit blocker when the text control has focus, and add some inputs.
        var parent_form = control_button.up('form');

        // If we don't have the coordinate inputs, we will create them.  If we do have elements
        // with inputs, we'll make sure they're elements we can use as inputs.
        if (!input_latitude) {
            var input_template = new Ext.DomHelper.Template('<input type="hidden" id="{0}" name="{0}" />');
    
            input_latitude = input_template.insertBefore(mapdiv.dom, [mapdiv.id + '-latitude'], true);
            input_longitude = input_template.insertBefore(mapdiv.dom, [mapdiv.id + '-longitude'], true);
    
        } else if (('input' != input_latitude.dom.tagName.toLowerCase()) || ('input' != input_longitude.dom.tagName.toLowerCase()) ||
            !(input_latitude.dom.type in {hidden:'', text:'', textarea:''}) ||
            !(input_latitude.dom.type in {hidden:'', text:'', textarea:''})) {
    
            // The elements wre either not input fields, or input fields that can't hold our
            // latitude and longitude values.
            OC.debug("GMap: Bad initialization coordinates");
            return;
        }

        // Create the controls used to update the map
        var control_text = Ext.get('geolocation');
        var control_error = Ext.get('oc-map-errors');

        // Function that takes a geocoder response and adjusts the map accordingly
        var updateMap = function(response) {
          if (!response || response.Status.code != 200) {
            control_error.update("Sorry, we were unable to find that address on the map");
          } else {
            map.clearOverlays();
            control_error.update('');
            var place = response.Placemark[0];
            var point = new GLatLng(place.Point.coordinates[1],
                                    place.Point.coordinates[0]);
            var marker = new GMarker(point, {draggable: !is_static_map});
            input_latitude.dom.value = point.lat();
            input_longitude.dom.value = point.lng();
    
            GEvent.addListener(marker, 'dragstart', function() {
                map.closeInfoWindow();
            });
        
            GEvent.addListener(marker, 'dragend', function() {
                control_error.update('');
                point = marker.getPoint();
                input_latitude.dom.value = point.lat();
                input_longitude.dom.value = point.lng();
            });
    
            map.setCenter(point, 15);
            map.addOverlay(marker);
            if( !is_static_map )
              marker.openInfoWindowHtml("Drag the pin to adjust location.",
                 {maxWidth: 180}); // @@ Broken! implicit minimum of 200!
          }
        }

        // We need a function that will take the desired text input, and submit it to Google
        // Maps.  Once we have it, we will set it up so that a click of the button or hitting
        // enter will perform the work.  In order to handle pressing enter, whenever the text
        // area has focus, we install a new submit handler for the parent form which cancels the
        // submit and instead performs the geocoding.  We remove this handler whenever the
        // text control loses focus.
        control_button.geocode = function() {
            var text = control_text.dom.value;
            text = Ext.util.Format.trim(text);
            if (text.length == 0) { 
                input_latitude.dom.value = '';
                input_longitude.dom.value = '';
                control_text.value = text;
                map.setCenter(default_point, 15);
            } else {
                geocoder.getLocations(text, updateMap);
            }
        }
        // Install click handler for the button
        control_button.addListener({scope: this,
            'click': control_button.geocode
        });

        // Install onfocus handler for the text control to handle the enter key.
        OC.SubmitBlocker.call(this, parent_form, control_text, control_button.geocode);
    
    }

    //map.enableScrollWheelZoom();

    // Try to get initialization coordinates
    var lat = input_latitude ? input_latitude.getValue() : '';
    var lon = input_longitude ? input_longitude.getValue(): '';

    if (is_static_map && ((0 == lat.length) || (0 == lon.length))) {
        mapdiv.dom.parentNode.removeChild(mapdiv.dom);
        return;
    }

    var map = new GMap2(document.getElementById(mapdiv.id));
    map.addControl(new GSmallMapControl());

    if ((0 == lat.length) || (0 == lon.length)) {
        // Lat/Lon of TOPP
        var center = default_point;
    } else {
        // We have preexisting coordinates, so we'll make a marker.
        var center = new GLatLng(lat, lon);
        var marker = new GMarker(center, {draggable: !is_static_map});
    }

    var dropHandler = function() {
        input_latitude.dom.value = this.getLatLng().lat();
        input_longitude.dom.value = this.getLatLng().lng();
    }

    map.setCenter(center, 15);

    if (typeof(marker) != 'undefined' && marker) {
        map.addOverlay(marker);
        if( !is_static_map )
          marker.openInfoWindowHtml("Drag the pin to adjust location.",
              {maxWidth: 180}); // @@ Broken, there's an implicit minimum of 200!
        GEvent.addListener(marker, 'dragend', dropHandler);
        GEvent.addListener(marker, 'dragstart', function () {
            map.closeInfoWindow();
        });
    }

    var geocoder = new GClientGeocoder();
};

/* 
   #
   # Member List
   #
   # Take's a comma separated list of members an turns it into a list control
   # that performs member validation.
*/
OC.MemberList = function(extEl) {
    // Get required elements
    var meminput = extEl;
    
    if (!meminput) {
        OC.debug("MemberList: Could not find list of members");
        return;
    } else if (('input' != meminput.dom.tagName.toLowerCase()) ||
              !(meminput.dom.type in {hidden:'', text:'', textarea:''})) {

        // The elements was either not an input fields or not one that can hold the member list.
        OC.debug("MemberList: Bad initialization coordinates");
        return;
    }

    // We're gonna hide the real form element we use from the user.
    meminput.setVisibilityMode(Ext.Element.DISPLAY);
    meminput.hide();

    // Create the list control used to update the member list
    var control_list = Ext.DomHelper.insertBefore(meminput.dom, {tag: 'ul', cls:'oc-plainList'}, true);

    // We need a function that will be able to remove members from the id list.
    control_list.member_remove = function(evt, memberEl, o) {
        // We'll grab the part of the element id after 'member-' (7 characters long)
        // which gives us the member id
        var memId = memberEl.parentNode.id.substring(7);

        // Regex that will properly remove the text from a comma separated list,
        // leaving the correct number of commas behind (one if it is in the middle of
        // the list, or none at either end)
        //                        |- One Element -|-  Beginning  -|-     End     -|-  Middle |
        var reRemove = new RegExp('^' + memId + '$|^' + memId + ',|,' + memId + '$|,' + memId);

        meminput.dom.value = meminput.dom.value.replace(reRemove, '');
        OC.Dom.removeItem (memberEl.parentNode.id);
    }

    // Template for creating list elements for each member.
    var list_member_template = new Ext.DomHelper.Template('<li id="member-{0}" ><a style="cursor: pointer">[ - ]</a> {0}</li>');

    // We'll use a regex to perform a string trim, since the function doesn't exist
    // in javascript. We've got to remember that split on an empty string returns
    // an array containing an empty string, not an empty array.
    var memarray = meminput.dom.value.length ? meminput.dom.value.split(',') : [];
    var reTrim = /^\s*\(.*\)\s*$/;
    for (var idxMember = 0; idxMember < memarray.length; ++idxMember) {
        memarray[idxMember] = memarray[idxMember].replace(reTrim, '\\1');
        var mem = list_member_template.insertFirst(control_list.dom, [memarray[idxMember]], true);
        Ext.EventManager.addListener(mem.dom.firstChild, 'click', control_list.member_remove);
    }

    // If there is a description tag, we'll hide it
    var desc = Ext.get(meminput.dom.parentNode).down('p.oc-js-memberList_description');
    desc.setVisibilityMode(Ext.Element.DISPLAY);
    desc.hide();


    var control_text = Ext.DomHelper.insertBefore(meminput.dom, {tag: 'input', type: 'text'}, true);
    var control_button = Ext.DomHelper.insertBefore(meminput.dom, {tag: 'input', type: 'button', value: 'Add'}, true);
    Ext.DomHelper.insertBefore(meminput.dom, {tag: 'br'});
    var control_error = Ext.DomHelper.insertBefore(meminput.dom, {tag: 'span', cls: 'oc-form-error'}, true);

    // If we have a parent form, we'll put in a submit blocker when the text control has focus
    var parent_form = meminput.up('form');

    // We need a function that will take the desired text input, and submit it to Google
    // Maps.  Once we have it, we will set it up so that a click of the button or hitting
    // enter will perform the work.  In order to handle pressing enter, whenever the text
    // area has focus, we install a new submit handler for the parent form which cancels the
    // submit and instead performs the geocoding.  We remove this handler whenever the
    // text control loses focus.
    control_button.member_add = function() {
        memarray = control_text.dom.value.split(',');
        var candidates = []
        for (var idxMember = 0; idxMember < memarray.length; ++idxMember) {
            memarray[idxMember] = memarray[idxMember].replace(reTrim, '\\1');

            // Build a regex that matches the token in a comma separated string
            var reMatch = new RegExp('(^|,)' + memarray[idxMember] + '(,|$)');

            if (!meminput.dom.value.match(reMatch)) {
                // If we don't already have it in our list of members, we'll look it up.
                candidates.push(memarray[idxMember]);
            }
        }
        control_text.dom.value = '';
        control_error.update('');
        if (!candidates.length) {
            return;
        }
        Ext.Ajax.request({
            url: location,
            params:'members=' + candidates.join(',') + '&task|validate-members=&mode=async',
            success:function(response, options) {
                // Clean the response, and remove any old error text
                var members = OC.CleanJSON(response.responseText)
                control_error.update('');

                for (var idxMember = 0; idxMember < members.valid.length; ++idxMember) {
                    // We need a comma if there are already values in the list
                    if (meminput.dom.value.length) {
                        meminput.dom.value += ',';
                    }
                    meminput.dom.value += members.valid[idxMember];

                    // Create the list element for the display, and attach a listener to the delete link.
                    var mem = list_member_template.insertFirst(control_list.dom, [members.valid[idxMember]], true);
                    Ext.EventManager.addListener(mem.dom.firstChild, 'click', control_list.member_remove);
                }
                if (members.rejects.length) {
                    control_text.dom.value = members.rejects.join(',');
                    control_error.update('The following members are invalid: "' + members.rejects.join(' ') + '"');
                }
            },
            failure:function(response, options) {
                control_error.update('Unable to validate members');
            },
            scope:this
        });
    }

    // Install click handler for the button
    control_button.addListener({scope: this,
        'click': control_button.member_add
    });

    // Install onfocus and onblur handlers for the text control to handle the enter key
    // if there is a containing form.
    OC.SubmitBlocker.call(this, parent_form, control_text, control_button.member_add);
};

OC.RevealElement = function(extEl) {
    // Any elements marked as oc-js-unhide will have that class removed.
    // Given appropriate css, this is the visual inverse of <noscript>.
    if (!extEl) {
         OC.debug("Unhide: Could not find element");
    } 
    extEl.removeClass('oc-js-unhide');
};

// Autosave the contents of the field, and restore if necessary
OC.CookieAutoSave = function(extEl) {
    if (!extEl.id) {
        return;
    }

    function get_cookie(cname) {
        // Make sure the document supports cookies
        if (!document || !document.cookie || (0 == document.cookie.length)) {
            return '';
        }

        // Look for the named cookie in the cookie list
        var start;
        if (-1 == (start = document.cookie.indexOf(cname + '='))) {
            return '';
        }

        // Point the index to the start of the value
        start += cname.length + 1;

        // Find the end of the cookie.  If it's the last cookie, there
        // is no delimiter string
        var end = document.cookie.indexOf(';', start);
        end = (-1 == end) ? document.cookie.length : end;

        return unescape(document.cookie.substring(start, end));
    }

    function set_cookie(name, value) {

        var cookie_string = name + "=" + escape(value);

        var expires = new Date();
        expires.setTime(expires.getTime() + 86400000);
        cookie_string += "; expires=" + expires.toGMTString();

        document.cookie = cookie_string;
    }

    function delete_cookie (cookie_name) {

        var cookie_date = new Date();  // current date & time
        cookie_date.setTime(cookie_date.getTime() - 1);
        document.cookie = cookie_name += "=; expires=" + cookie_date.toGMTString();
    }

    var cookie_name = 'autosave#' + extEl.id;
    var autosave = get_cookie(cookie_name);

    if (autosave.length) {
        extEl.dom.value = autosave;
        delete_cookie(cookie_name);
    }

    extEl.dom.enable_autosave = true;
    extEl.dom.autosave = function() {
    	if (!extEl.dom.enable_autosave) {
            return;
	}
        setTimeout(extEl.dom.autosave, 500); // Autosave once a second
        if (!extEl.dom.value.length) {
            return;
        }
        set_cookie(cookie_name, extEl.dom.value);
    }
    extEl.dom.disable_autosave = function() {
        extEl.dom.enable_autosave = false;
        delete_cookie(cookie_name);
    }

    // On submit, we'll clear the cookie,,,
    var parentForm = extEl.findParentNode('form');
    if (parentForm) {
        Ext.get(parentForm).addListener('submit', extEl.dom.disable_autosave);
    }

    setTimeout(extEl.dom.autosave, 500); // Autosave once a second
};

// Add a 'password' hint to compact login forms
OC.CompactPassword = function(passField) {
    // Prettify inline password fields 
    if( document.createElement && document.childNodes ) { 

        // We'll create an input text element to mirror the password, copying
        // the password element's classes.  The shadow text element will have
        // the text 'password' inside, and will switch itself out with the real
        // password element when focused.  If the password field is left blank
        // when focus is lost, then the hint field will be restored.
        var hintField = document.createElement('input'); 
        hintField.setAttribute('type','text'); 
        hintField.setAttribute('value','password'); 
        hintField.setAttribute('class',passField.dom.className); 
        // We have to set both cases of this property to support all browsers
        hintField.setAttribute('tabindex',passField.dom.tabIndex); 
        hintField.setAttribute('tabIndex',passField.dom.tabIndex); 

        // Place the hint field just before the real field
        passField.dom.parentNode.insertBefore(hintField, passField.dom); 

        // Turn our reference into an Ext.Element to make it easier to work with
        hintField = Ext.get(hintField); 

        // Set up both fields to use the display propert for visibility
        passField.enableDisplayMode(); 
        hintField.enableDisplayMode(); 

        // Hide the password field and show the hint field if the password
        // field is empty
        if ('' == passField.dom.value) {
            passField.hide(); 
            hintField.show(); 
        } else {
            passField.show(); 
            hintField.hide(); 
        }

        // When clicking on the hint field, we want to replace it with the real
        // password field, and be sure it receives the focus, so as not to
        // confuse the user.
        hintField.addListener('focus', function() { 
            hintField.hide(); 
            passField.show(); 
            passField.focus(); 
        }); 

        // When losing focus, we only restore the hint field if there is no
        // password entered into the field.
        passField.addListener('blur', function() { 
            if (passField.dom.value != '') { 
                return; 
            } 
            hintField.show(); 
            passField.hide(); 
        }); 
    } 
};

// modify the add a wiki page link into a form
// that performs the submission to create the page
OC.AddWikiPage = function(extEl) {
    var parent_div = extEl.up('div');
    var anchor = extEl;
    if (!parent_div) {
        return;
    }
    anchor.on('click', function(e, el, o) {
        // XXX Ext has a real nice api for creating forms
        // I tried using them here, but got an undefined for
        // Ext.form.Form and Ext.form.BasicForm
        // maybe when we upgrade we'll get to use those
        cancel = Ext.DomHelper.append(parent_div,
            { tag: 'a', cls: 'oc-banana', href: '#' }, true);
        cancel.dom.innerHTML = 'Cancel';
        form_div = Ext.DomHelper.append(parent_div,
            { tag: 'div', style: 'margin-bottom: .5em' });
        form = Ext.DomHelper.append(form_div,
            { tag: 'form', method: 'POST', action: el.href },
            true)
        title_label = Ext.DomHelper.append(form, {
            tag: 'label', htmlFor: 'page_title', html: 'Title',
            style: 'margin-right: .5em'});
        title_input = Ext.DomHelper.append(form, {
            tag: 'input', type: 'text', id: 'page_title', name: 'title',
            style: 'margin-right: .5em; width: 60%' });
        btn = Ext.DomHelper.append(form,
            { tag: 'input', type: 'submit', name: 'add', value: 'Add' });

	    Ext.get(form_div).slideIn('t',{duration: .1});

        // focusing the textfield makes this much more usable
        setTimeout('Ext.get(title_input).focus()', 150);

        // XXX it would be nice to also provide inline validation to make sure
        // that the title of the page was specified and is unique

        // and we remove the link so the user can't add another form
        // afaict, it doesn't hurt to leave the form on the page if the user
        // changes their mind and no longer wants to add a page
        // so I don't think we need to provide a mechanism for the user to
        // cancel, which reverts back to the anchor and removes the form
        anchor.setVisibilityMode(Ext.Element.DISPLAY);
        anchor.hide();

        cancel.on('click', function(e, el, o) {
          anchor.show();
          cancel.remove();
          Ext.get(form_div).remove();
        }, this, {preventDefault: true});
    }, this, {preventDefault: true});
};

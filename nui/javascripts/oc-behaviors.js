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
OC.liveElementKey = {
    'input[type=text]'        : 'FocusField',
    'input[type=password]'    : 'FocusField',
    'input[type=file]'        : 'FocusField',
    'textarea'                : 'FocusField',
    ".oc-js-autoSelect"       : "AutoSelect",
    ".oc-js-expander"         : "Expander",
    "#version_compare_form"   : "HistoryList",
    ".oc-widget-multiSearch"  : "SearchLinks",
    '.oc-dropdown-container'  : "DropDown",
    '#oc-project-create'      : "ProjectCreateForm",
    ".oc-autoFocus"           : "AutoFocus",
    ".oc-warn-popup"          : "WarnPopup",
    '.oc-checkAll'            : "CheckAll",
    '.oc-js-liveEdit'         : "LiveEdit",
    '.oc-js-actionLink'       : "ActionLink",
    '.oc-js-actionButton'     : "ActionButton",
    '.oc-js-actionSelect'     : "ActionSelect",
    '.oc-js-liveValidate'     : "LiveValidatee",
    ".oc-js-closeable"        : "CloseButton",
    '#oc-content-wrapper'     : "AutoHeightContent"
};
    
/* 
   # breathes life (aka js behaviors) into HTML elements.  call this on
   # load w/ no argument to breathe life to entire document.  When adding
   # new nodes to the dom, call breatheLife(newItem) to activate that
   # element and its children.
*/
OC.breatheLife = function(newNode, force) {
  OC.debug("START BreatheLife");
  
  // force re-up?
  if (typeof force == "undefined") { force = false }
  
    // set scope
    if (!newNode) {
	   targetNode = document;
    } else {
      // accept HTML element or Ext Element
      if (newNode.dom)
          targetNode = newNode.dom;
      else 
          targetNode = newNode; 
    }
    
    // loop through selectors specified above
    for (var selector in OC.liveElementKey) {
	
      // Get array of elements to apply behaviors to.  Include newNode itself in query.      
      var elements = Ext.query(selector, targetNode);
      if (Ext.DomQuery.is(targetNode, selector)) {
          elements.push(Ext.get(targetNode));
      }
	
      if(elements.length > 0){
          
       for (var i = 0; i < elements.length; i++) {
        
          //get an Ext Obj for your element
          var extEl = Ext.get(elements[i]);
          
          //get reference to the proper constructor
          var constructor = OC[this.liveElementKey[selector]]; 
          var constructorName = this.liveElementKey[selector]; 
          
          // make a new liveElements array for this ID
          if (typeof OC.liveElements[extEl.id] == "undefined" ) {
            OC.liveElements[extEl.id] = {};      
          }
                
          // add a new liveElement to OC.liveElements.
          // only make a new one if it doesn't exist, or if force has been specified
          OC.debug("BreatheLife: Considering making " + " Constructor: " + this.liveElementKey[selector] + " ID: " + extEl.id)
          
          if (force || typeof OC.liveElements[extEl.id][constructorName] == "undefined" ) {
             OC.debug("BreatheLife: Starting new element. " + " Constructor: " + this.liveElementKey[selector] + " ID: " + extEl.id);
              var myId = extEl.id;
              OC.liveElements[myId][constructorName] = new constructor(extEl);
          }
        } // end for each element
      } // end if there are elements
    } // end for each selector
  OC.debug(OC.liveElements);
  OC.debug("END BreatheLife");

}; // OC.breatheLife()

/*
  #------------------------------------------------------------------------
  # Utilities
  #------------------------------------------------------------------------
*/

// Debug Function.  Turn off for live code or IE
OC.debug = function(string) {
    if( typeof console != 'undefined' ) {
	console.log(string);
    }
};

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
    OC.liveElements[extEl.id] = {};
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
    
    
    try {  this.indicator.hide();  } catch(err) { OC.debug(err); }
    try {  this.button.dom.value = this.origButtonValue; this.button.dom.disabled = false;  } catch(err) { OC.debug(err); }
    
    Ext.select('form').each(function(el) {
	    el.dom.target = "";
	});
    OC.debug('OC.Callbacks.afterAjaxSuccess');
    OC.debug('o: ' + o);
    
    var response;
    // trim response text to avoid errors in IE
    var responseText = o.responseText.replace(/[\r\n]/g, "");
    OC.debug(responseText);

    //var updater = new OC.Updater();
    
    try {
      response = eval( "(" + responseText + ")" );
    } catch( e ) {
      OC.debug(e);
      OC.debug("Couldn't parse the response.  Bad JSON? (below): ");
	    OC.debug(responseText);
	    OC.psm('There was an error handling the Ajax response.  Ethan will fix it. ', 'bad')
    }
    
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
	case "delete":
	    OC.debug("DELETE on " + elId);
	    OC.Dom.removeItem(elId);
	    break;
	    
	case "replace":
	    var html, effects;	    	    
	    if( typeof command == "string" ) { // for backcompability with existing code. consider deprecated.		
		html = command;
		if( action == "update" )
		    effects = "highlight";
      else if( action == "uploadAndUpdate" )
		    effects = "fadeIn";
	    } else if( typeof command == "object" ) {
        effects = command.effects;
        html = command.html;
	    }
	    OC.debug("REPLACE " + elId + " with " + html + " using effect " + effects);
	    
	    html = Ext.util.Format.trim(html);
	    var target = Ext.get(elId);
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
	} // end switch on actio
    } // end for each element
}; // end OC.Callbacks.afterAjaxSuccess()

OC.Callbacks.afterAjaxFailure = function(o) {
    OC.debug('OC.Callbacks.afterAjaxFailure');
    OC.debug(o.responseText);
    OC.psm('There was a problem with the AJAX Request.  Octopus!', 'error');
};

/*
  #------------------------------------------------------------------------
  # Classes - will become liveElement objects
  #------------------------------------------------------------------------
*/

/* 
   #
   # Action Links
   #
*/
OC.ActionLink = function(extEl) {
    // get refs
    link = extEl;
    this.button = link; /* for ajax callback */
    this.origButtonValue = this.button.dom.innerHTML; /* for ajax callback */
    
    if (!link) {
	     OC.debug("ActionLink: Could not get refs");
    } else {
	     OC.debug("ActionLink: Got refs")
    }
    
    function _doAction(e, el, o) {
	YAHOO.util.Event.stopEvent(e);
	
	// get action/href & split action from params
	var action = el.href.split("?")[0];
	var requestData = el.href.split("?")[1];
	OC.debug("request data is " + requestData);
	
	var requestUri = el.href + "&mode=async";
	
	this.button.dom.innerHTML = "Please wait..."; 
	
	// make connection
	var cObj = YAHOO.util.Connect.asyncRequest("GET", requestUri, {
		success: OC.Callbacks.afterAjaxSuccess, 
		failure: OC.Callbacks.afterAjaxFailure,
		scope: this 
	    });
    } 
    link.on('click', _doAction, this);
    
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
    var submit = Ext.get(Ext.query('input[type=submit]', container.dom)[0]);
    submit.hide();
    var form = select.up('form');
    
    //check refs
    if (!select) {
	OC.debug("ActionSelect: Couldn't get refs");
	return;
    } else {
	OC.debug("ActionSelect: Got Refs");
    }
    
    //settings
    var action = form.dom.action;
    var orig_task = submit.dom.name;
    var task = submit.dom.name;

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
    select.on('change', _doAction, this);
    
    // pass back element to OC.LiveElements
    return this;
};

/* 
   #
   # Action Buttons
   #
*/
OC.ActionButton = function(extEl) {
    // get refs
    this.button = extEl;
    var form = this.button.up('form');
    var name = this.button.dom.name.replace('task|', "");
    this.indicator = Ext.get('indicator|' + name);
        
    // check refs
    if (!this.button || !form) {
      OC.debug("ActionButton: Couldn't get refs");
      return;
        } else {
      OC.debug("ActionButton: Got Refs");
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
    }
    this.button.on('click', _actionButtonClick, this);
    
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
    } else {
	OC.debug("CheckAll: Got refs");
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
  # Live Validatee
  #
*/
OC.LiveValidatee = function(extEl) {
    // get refs
    var field = extEl;
    var form = field.up('form');
    
    function _validateField(e, el, o) {
	
	var request = "";
	for (var i=0; i<form.dom.elements.length; i++) {
	    var input = form.dom.elements[i];
	    if (input.value && input.type != 'submit') {
		OC.debug(form.dom.elements[i]);
		request += form.dom.elements[i].name + "=" + form.dom.elements[i].value + "&";
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
    var submit = Ext.get(Ext.query('input[type=submit]',form.dom)[0])
    
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
    form.on('submit', _formSubmit, this);
    
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
        } else {
      OC.debug("TopNav: got refs");
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
      OC.debug(overrideHide);
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
  # Auto Height Content
  #
*/
OC.AutoHeightContent = function(extEl) {
  // get refs
  var content = extEl;
  
  // check refs
  if (!content) {
    OC.debug("AutoHeightContent: couldn't get refs");
  } else {
    OC.debug("AutoHeightContent:  got refs");
  }
  
  // settings
  var currentHeight = content.dom.offsetHeight;
  
  if (currentHeight < 430) {
    content.dom.style.height = "430px";
  }  
  
  return this;
}

/* 
   #
   #  Project Create Form
   #
*/
OC.ProjectCreateForm = function(extEl) {
    // get refs
    var form = extEl;
    var nameField = Ext.get(Ext.query('#title')[0], form.dom);
    var urlField = Ext.get(Ext.query('#id')[0], form.dom);
    
    // check refs
    if (!form || !nameField || !urlField) {
	     OC.debug("ProjectCreateForm: couldn't get refs");
    } else {
	     OC.debug("ProjectCreateForm: got refs");
    }
    
    // settings & properties
    /* has the user manually overridden our suggested url? */
    var customUrl = false;
    
    // suggested URL
    var suggestedUrl = "";
    
    function _urlize(e, el, o) {
      if (!customUrl) {
          suggestedUrl = Ext.util.Format.trim(el.value).toLowerCase().replace(/[^a-zA-Z0-9-\s]/gi, "").replace(/  /g, " ").replace(/ /g, "-");
          OC.debug(suggestedUrl);
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
    if (hideFormLink.elements.length == 0) hideFormLink = Ext.get(document.body);
        
    if (!value || !editForm) {
        OC.debug("liveEdit: Couldn't get element refs");
        return;
    } else {
      OC.debug('LiveEdit: got element refs');
    }
    
    // settings
    value.setVisibilityMode(Ext.Element.DISPLAY);
    editForm.setVisibilityMode(Ext.Element.DISPLAY);
    editForm.hide();
    var hideThisForm = false;
    
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
          if (Ext.get(el).hasClass('oc-js-liveEdit_hideForm')) {
            e.preventDefault();
          }
          OC.debug('_hideForm');
          value.show();
          editForm.hide();
        }
        hideThisForm = false;
    }
    function _showForm(e) {
        e.stopEvent();
        OC.debug('_showForm');
        value.hide();
        editForm.show();
        hideThisForm = true;
        var form = Ext.get(Ext.query('input[type=text]', editForm.dom)[0]) || Ext.get(Ext.query('select', editForm.dom)[0]);
        if (form) { form.focus(); }
    }
    
    
    // liveEdit value behaviors
    function _valueMouseover(e, el, o) {
        value.addClass('oc-liveEdit-hover');
        if (hoverShowFormLink) hoverShowFormLink.hide();
    }
    value.on('mouseover', _valueMouseover, this);
    
    function _valueMouseout(e, el, o) {
        value.removeClass('oc-liveEdit-hover');
        if (hoverShowFormLink) hoverShowFormLink.hide();
    }
    value.on('mouseout', _valueMouseout, this);
    
    
    if (showFormLink) {
      showFormLink.on('click', _showForm, this, {stopPropagation: true});
    }
    if (hoverShowFormLink) { 
      hoverShowFormLink.on('click', _toggleForm, this);
    }
    if (hideFormLink) {
        hideFormLink.on('click', _hideForm, this);
    }
    
    return this;
};

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
    } else {
	OC.debug("SearchLinks: got element refs");
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
OC.WarnPopup = function(extEl) {
    var msg = "Removing this feature may result in lost data for your project."
    msg += " Are you sure you want to remove the feature?"
    var item = Ext.get(extEl);
    //behaviors
    function _itemClick(e, el, o) {
	if( !item.dom.checked )
	    if( !confirm(msg) )
		YAHOO.util.Event.stopEvent(e);
    }
    item.on('click', _itemClick, this);
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
    var submit = Ext.get(Ext.query('input[type=submit]', form)[0]) || Ext.get(Ext.query('button[type=submit]', form)[0]);
    
    
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
    select.on('change', _selectChange, this);
    
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
    OC.debug("OC expander is good " + extEl);
    
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
  # History List
  #
*/
OC.HistoryList = function(extEl) {
    // setup references
    var form = extEl;
    var compareButtons = Ext.select('#' + form.dom.id + ' input[type=submit]');
    var versions  = Ext.get(Ext.select('#' + form.dom.id + ' li'));
    var checkboxes = Ext.get(Ext.select('#' + form.dom.id + ' input[type=checkbox]'));
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

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
 OC.liveElements = new Array();
    
/* 
#
# how we know which elements get which features
# css or xpath selector : OC Object name (without OC.)
#
*/
OC.liveElementKey = {
  ".oc-uploadForm" : "UploadForm",
  ".oc-liveEdit" : "LiveEdit",
  ".oc-close" : "CloseButton",
  ".oc-autoSelect" : "AutoSelect",
  ".oc-expander" : "Expander",
  "#version_compare_form" : "HistoryList",
  "#oc-join-form" : "JoinForm",
  ".oc-liveForm" : "LiveForm",
  ".oc-liveItem" : "LiveItem",
  ".oc-widget-multiSearch" : "SearchLinks",
  '#oc-usermenu-list' : "TopNav",
  '#oc-project-create' : "ProjectCreateForm",
  ".oc-autoFocus" : "AutoFocus"
}
    
/* 
# breathes life (aka js behaviors) into HTML elements.  call this on
# load w/ no argument to breathe life to entire document.  When adding
# new nodes to the dom, call breatheLife(newItem) to activate that
# element and it's children.
*/
OC.breatheLife = function(newNode) {

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
      elements.push(Ext.get(targetNode))
    }
    
    if(elements.length > 0){
      
      for (var i = 0; i < elements.length; i++) {
      
        //get an Ext Obj for your element
        var extEl = Ext.get(elements[i]);
        
        //get reference to the proper constructor
        var constructor = OC[this.liveElementKey[selector]];        
        
        // add a new liveElement to OC.liveElements
        OC.liveElements[extEl.dom.id] = new constructor(extEl);
        
      }
    }      
  }
  
  OC.debug(OC.liveElements);

} // OC.breatheLife()

/*
#------------------------------------------------------------------------
# Utilities
#------------------------------------------------------------------------
*/

// Debug Function.  Turn off for live code or IE
OC.debug = function(string) {
    if( typeof console != 'undefined' )
	console.log(string);
}

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
# Classes - will become liveElement objects
#------------------------------------------------------------------------
*/

/*
#
# Live Form
# Takes a standard HTML Form and allows you to submit part or all of it via Ajax.
#
*/
OC.LiveForm = function(extEl) {

  // get references
  var liveForm = extEl;
  var actionLinks = Ext.select('.oc-actionLink');
  var actionSelects = Ext.select(".oc-actionSelect");
  var checkAll = Ext.select(Ext.query('.oc-checkAll', liveForm.dom));
  var liveItems = Ext.query(".oc-liveItem", liveForm.dom);
  var liveValidatees = Ext.get(Ext.query('.oc-liveValidate', liveForm.dom));

  OC.debug(liveValidatees);

  // check required refs
  if (!liveForm) {
    OC.debug("LiveForm: couldn't get element references")
    return;
  }  else {
    OC.debug('LiveForm: Got element references');
  }
  
  // properties & settings
  var updater = {
    task : null,
    target : null
  }
  var requestData = null; /* request params, once an action happens */
  var isUpload = false;
    
  // helper function to get update target
  function _getUpdater(requestData) {
    OC.debug("_getUpdater");
    var data = requestData.split("&");
    for (var i = 0; i<data.length; i++) {
      item = data[i].split('=');
      
      if (item[0] == "task") {
        var target_task  = item[1].split('_');
          updater.target = Ext.get(target_task[0]) || target_task[0];
          updater.task = target_task[1];
      }
    }
    if (updater.task == "uploadAndUpdate" || updater.task == "uploadAndAdd") {
      isUpload = true;
    }
  }
  
  // check all box
  if (checkAll) { 
    checkAll.removeAllListeners();
    function _checkAllClick(e, el, o) {
      OC.debug('_checkAllClick');
      var boxes = Ext.select(Ext.query('input[type=checkbox]', liveForm.dom));
      if (el.checked) {
        boxes.set({checked: true}, false);
      } else {
        boxes.set({checked: false}, false);
      }
    }
     
     checkAll.on('click', _checkAllClick, this); 
  }  
  
  // live validatees
  if (liveValidatees) {    
    function _validateField(e, el, o) {
      YAHOO.util.Event.stopEvent(e);
      
      var request = "";
      for (var i=0; i<liveForm.dom.elements.length; i++) {
	  input = liveForm.dom.elements[i];
	  if (input.value && input.type != 'submit') {
	      OC.debug(liveForm.dom.elements[i]);
	      request += liveForm.dom.elements[i].name + "=" + liveForm.dom.elements[i].value + "&";
	  }
      }      
      
      // send ajax request
      var action = liveForm.dom.action;
      
      var cObj = YAHOO.util.Connect.asyncRequest("POST", action, 
        { success: _afterValidateSuccess, 
          failure: _afterValidateFailure, 
          scope: this 
        },
        request + "only_validate=True"
      );

    }
    liveValidatees.on('blur', _validateField, this);
    
    function _afterValidateSuccess(o) {
        OC.debug('_afterValidateSuccess');
    
        var response = eval( "(" + o.responseText + ")" );
        
        /* FIXME: What if this is an error page? (404, need login, etc) */
        /* Response is an array.  [elementID : newHTML] */
        for (elId in response) {
          var field = Ext.get(elId);
          var validator = Ext.get("oc-" + elId + "-validator");
          var message = Ext.util.Format.trim(response[elId]);
          validator.update(message);
        }
    }
    function _afterValidateFailure(o) {
    
    }
    
  }
  
  
  // action links
  if (actionLinks) {
    actionLinks.removeAllListeners();;
    function _actionLinkClick(e, el, o) {
      YAHOO.util.Event.stopEvent(e);
      
      // get action/href & split action from params
      var action = el.href.split("?")[0];
      requestData = el.href.split("?")[1];
      OC.debug("request data is " + requestData);
      updater = _getUpdater(requestData);
      var requestUri = el.href + "&mode=async";
      
      // make connection
      var cObj = YAHOO.util.Connect.asyncRequest("GET", requestUri, 
        { success: _afterSuccess, 
          failure: _afterFailure, 
          scope: this 
        }
      );
    } 
    actionLinks.on('click', _actionLinkClick, this);
  }
    
  // process action select boxes
  if (actionSelects) {
    actionSelects.removeAllListeners();;
    function _actionSelectChange(e, el, o) {
      YAHOO.util.Event.stopEvent(e);

      // get action from form element
      var action = liveForm.dom.action;
      OC.debug("form action: " + action);
      var submit = document.createElement('input');
      submit.name = "task";
      submit.value = el.id;
      OC.debug("task info: " + el.id);
      submit.type = "hidden";
      liveForm.dom.appendChild(submit);

      YAHOO.util.Connect.setForm(liveForm.dom);
      var cObj = YAHOO.util.Connect.asyncRequest("POST", action, 
        { success: _afterActionSelects,
          failure: _afterFailure,
          scope: this
        },
        "mode=async"
      );

      submit.parentNode.removeChild(submit);
    }
    actionSelects.on('change', _actionSelectChange, this);
  }


  // after successful actionSelects
  function _afterActionSelects(o) {
    var response = o.responseText;  //o.responseText;
    var psm = document.createElement('div');
    psm.className = "oc-statusMessage";
    var psm_text = document.createTextNode(response);
    psm.appendChild(psm_text);
    var psm_container = document.getElementById('oc-statusMessage-container');
    psm_container.appendChild(psm);
  }

  // form submit
  function _formSubmit(e, el, o) {
    OC.debug("_formSubmit");
    
    requestData = YAHOO.util.Connect.setForm(liveForm.dom);
    updater = _getUpdater(requestData);

    if (isUpload) 
        YAHOO.util.Connect.setForm(liveForm.dom, true);

    // XXX todo -- this is no good -- 
    // don't want the task to have to talk to JS at all really
    //if (updater.task && updater.task != "noAjax") {
      YAHOO.util.Event.stopEvent(e);
      var action = liveForm.dom.action;
      var cObj = YAHOO.util.Connect.asyncRequest("POST", action, 
        { success: _afterSuccess, 
          upload: _afterSuccess,
          failure: _afterFailure, 
          scope: this 
        },
        "mode=async"
      );
    //}
  }
  liveForm.on('submit', _formSubmit, this);


  // after success
  function _afterSuccess(o) {
    OC.debug('_afterSuccess');
    OC.debug('o: ' + o);

    var response;
    try {
	response = eval( "(" + o.responseText + ")" );
	OC.debug(response);
    } catch( e ) {
	OC.debug("Couldn't parse response " + o.responseText + " . Is it bad JSON?")
    }

    if( response instanceof Array ) { 	// for backcompatibility with existing code. consider deprecated.
	// we will translate the array into an object 
	// with "delete" actions for each elId, since
	// that's the only case where we used to expect an array.
	var newResponse = {};
	for( var iter = 0; iter < response.length; ++iter ) {
	    newResponse[response[iter]] = {'action': 'delete'};
	}
	response = newResponse;
    }

    for( elId in response ) {
	var command = response[elId];
	var action = command.action;
	if( !action ) {   // for backcompability with existing code. consider deprecated.
	    action = updater.task;
	}
	
	switch( action ) {
	case "delete":
	    OC.debug("DELETE on " + elId);
	    _removeItem(elId);
	    break;

	case "update": // for backcompability with existing code. consider deprecated.
	case "uploadAndUpdate": // for backcompability with existing code. consider deprecated.
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
	    
	    if( effects == "delete" ) {  // for backcompability with existing code. consider deprecated.
		_removeItem(elId);
	    } else {
		var newNode = Ext.DomHelper.insertHtml("beforeBegin", target.dom, html);
		target.remove();

		if( effects == "highlight" ) {
		    Ext.get(newNode).highlight();
		}

		OC.debug("about to breathe life into EVERYTHING. this is bad");
		OC.breatheLife();
		OC.debug("done breathing");
	    }
	    break;

	case "uploadAndAdd": // for backcompability with existing code. consider deprecated.
	    OC.debug('_afterSuccess, task: uploadAndAdd');
	    break;

	case "copy": // fill me in: replace target's children with html
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
	}
    } 
  }
  
  // after failure
  function _afterFailure(o) {
    OC.debug('_afterFailure');
  }
  
  // remove item
  function _removeItem(id) {
    var extEl = Ext.get(id);
    if (!extEl) {
	OC.debug("Could not find an element #" + id);
	return;
    }
    extEl.fadeOut({remove: true, useDisplay: true});
    
    // to do: send user message w/ undo link
  }
  
  return this;
}

/* 
#
# Auto Focus
# 
# 
*/
OC.AutoFocus = function(extEl) {
  // get refs
  extEl.dom.focus();
}


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
}

/*
#
# Top Nav
#
*/
OC.TopNav = function(extEl) {
  // get refs
  var container = extEl;
  var triggerItem = Ext.get(extEl.dom.getElementsByTagName('li')[0]);
  var triggerLink = Ext.get(triggerItem.dom.getElementsByTagName('a')[0]);
  var menu = Ext.get(triggerItem.dom.getElementsByTagName('ul')[0]);
  var unclickArea = Ext.get(document.body);
  OC.debug(unclickArea);
  
  // check refs
  if (!container || !triggerItem || !menu) {
    OC.debug("TopNav: couldn't get refs");
    return;
  } else {
    OC.debug("TopNav: got refs");
  }
  
  // settings
  var overrideHide = false;
    
  function _toggleMenu(e, el, o) {
    //YAHOO.util.Event.stopEvent(e);
    
    if (menu.isVisible() && el.tagName != "A") {
      _hideMenu(e);
    } else {
      _showMenu(e); 
    }
  }
  
  function _showMenu(e, el, o) {
    //YAHOO.util.Event.stopEvent(e);
    OC.debug('_showMenu: ');
    overrideHide = true;
    menu.show();
    triggerItem.addClass('oc-selected');
  }
  
  function _hideMenu(e, el, o) {
    if (menu.isVisible() && !overrideHide) {
          menu.hide();
          triggerItem.removeClass('oc-selected');
    }
    overrideHide = false;
  }
  //exploreMenu.on('mouseout', _hideExplore, this);
  
  function _toggleMenuPreview(e, el, o) {
    if (triggerItem.hasClass('oc-hover')) {
       triggerItem.removeClass('oc-hover');
    } else {
      triggerItem.addClass('oc-hover');
    }
   
  } 
  triggerItem.on('mouseover', _toggleMenuPreview, this);
  triggerItem.on('mouseout', _toggleMenuPreview, this);
  
  unclickArea.on('click', _hideMenu, this );
  triggerItem.removeListener('click', _hideMenu);
  triggerItem.on('click', _toggleMenu, this, { stopPropogation: true});


}


/* 
#
#  Project Create Form
#
*/
OC.ProjectCreateForm = function(extEl) {
  // get refs
  var form = extEl;
  var nameField = Ext.get(Ext.query('#full_name')[0], form.dom);
  var urlField = Ext.get(Ext.query('#title')[0], form.dom);
  
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
       suggestedUrl = Ext.util.Format.trim(el.value).toLowerCase().replace(/[^a-zA-Z0-9\s]/gi, "").replace(/  /g, " ").replace(/ /g, "-");
       OC.debug(suggestedUrl);
       urlField.dom.value = suggestedUrl;
    } else {
      OC.debug('custom URL: will not suggest'); 
    }
  }
  nameField.on('keyup', _urlize, this);
  
  function _checkForCustomUrl(e, el, o) {
    if (el.value != suggestedUrl) {
      customUrl = true;
      OC.debug('custom url')
    }
  }
  urlField.on('keyup', _checkForCustomUrl, this);
  
  /* TO DO: Validate project url via Ajax
  #  title field: onblur
  #  url field: onkeyup
  #
  */  


}// end OC.ProjectCreateForm()

/* 
#
# Live item
# Show/hide editable version of a value.  
# LiveItems should always be part of a LiveForm.
# FIXME: Replace LiveEdit with LiveItem + LiveForm
#
*/
OC.LiveItem = function(extEl) {

      // get references
      var value = Ext.get(Ext.query('.oc-liveItem-value', extEl.dom)[0]); 
      var directEdit = Ext.get(Ext.query('.oc-liveItem-directEdit', extEl.dom)[0]);
      var editForm = Ext.get(Ext.query('.oc-liveItem-editForm', extEl.dom)[0]);
      var showFormLink = Ext.select(Ext.query('.oc-liveItem_showForm', extEl.dom));
      var hoverShowFormLink = Ext.select(Ext.query('.oc-liveItem_hoverShowForm', extEl.dom));
      var cancelLink = Ext.select(Ext.query('.oc-liveItem_cancel', extEl.dom));
      
      if (!value || !editForm) {
        OC.debug("liveItems.each: Couldn't get element refs");
        return;
      }
      
      // remove listeners.  For when we re-breathe life
      value.removeAllListeners();
      editForm.removeAllListeners();
      showFormLink.removeAllListeners();
      hoverShowFormLink.removeAllListeners();
      cancelLink.removeAllListeners();
      
      // settings
      value.setVisibilityMode(Ext.Element.DISPLAY);
      editForm.setVisibilityMode(Ext.Element.DISPLAY);
      editForm.hide();
      hoverShowFormLink.hide();
      
      function _toggleForm() {
        OC.debug('_toggleForm');
        value.toggle();
        editForm.toggle();
      }
      
      // liveEdit value behaviors
      function _valueMouseover(e, el, o) {
        value.addClass('oc-liveItem-hover');
        if (hoverShowFormLink)
          hoverShowFormLink.show();
      }
      value.on('mouseover', _valueMouseover, this);
      
      function _valueMouseout(e, el, o) {
        value.removeClass('oc-liveItem-hover');
        if (hoverShowFormLink)
          hoverShowFormLink.hide();
      }
      value.on('mouseout', _valueMouseout, this);
      
      //value.on('click', _toggleForm, this);
      
      if (directEdit) {
        directEdit.on('click', _toggleForm, this);
      }
      
      // toggle link
      function _toggleLinksClick(e, el, o) {
        YAHOO.util.Event.stopEvent(e);
        _toggleForm();
      }
      showFormLink.on('click', _toggleLinksClick, this);
      hoverShowFormLink.on('click', _toggleLinksClick, this);
      cancelLink.on('click', _toggleLinksClick, this);
      
      return this;
}


/*
#
# Live Edit Forms
#
*/
OC.LiveEdit = function(extEl) {
    //get references for included elements
    var container = extEl;
    var value = Ext.select(Ext.DomQuery.select('.oc-liveEdit-value', container.dom));
    var edit = Ext.get(Ext.query('.oc-liveEdit-edit', container.dom)[0]);
    var delete_ = Ext.get(Ext.query('.oc-liveEdit-delete', container.dom)[0]);
    var form = Ext.get(Ext.query('.oc-liveEdit-form', container.dom)[0]);
    var cancel = Ext.get(Ext.query('.oc-liveEdit-cancel', container.dom)[0]);

    // check to make sure we have what we need
    //if(!this.container || !this.value || !this.form)
    //    return;

    OC.debug(form.dom);

    /*
     # Attach Behaviors
     */
    // container
    function _containerMouseOver(e, el, o) {
        container.addClass('oc-liveEdit-hover');
        value.addClass('oc-liveEdit-hover');
    }
    container.on('mouseover', _containerMouseOver, this);

    function _containerMouseOut(e, el, o) {
        container.removeClass('oc-liveEdit-hover');
        value.removeClass('oc-liveEdit-hover');
    }
    container.on('mouseout', _containerMouseOut, this);

    //edit
    function _editClick(e, el, o) {
        YAHOO.util.Event.stopEvent(e);
        value.hide();
        form.show();
        container.addClass('oc-liveEdit-editing');
    }
    if (edit) {
        edit.on('click', _editClick, this);
    }

    function _deleteClick(e, el, o) {
        YAHOO.util.Event.stopEvent(e);
        if (confirm("Are you sure you want to delete?")) {
            YAHOO.util.Connect.setForm(form.dom);
            var action = form.dom.action.replace(/(.*)update/, '$1delete');
            var cObj = YAHOO.util.Connect.asyncRequest("POST", action, { success: _afterDelete, failure: _afterFailure, scope: this });
        }            
    }
    if (delete_) {
        delete_.on('click', _deleteClick, this);
    }


    //value
    value.setVisibilityMode(Ext.Element.DISPLAY);

    //form
    form.setVisibilityMode(Ext.Element.DISPLAY);
    form.hide();

    //ajax request
    _formSubmit = function(e, el, o) {
        YAHOO.util.Connect.setForm(el);
        var cObj = YAHOO.util.Connect.asyncRequest("POST", el.action, { success: _afterSuccess, failure: _afterFailure, scope: this });
        YAHOO.util.Event.stopEvent(e);
    }
    form.on('submit', _formSubmit, this);

    // after request

    function _afterDelete(o) {
        // delete original container
        container.setVisibilityMode(Ext.Element.DISPLAY);
        container.dom.style.backgroundColor = "red";
        container.fadeOut();
    }

    function _afterSuccess(o) {

        // insert new - DomHelper.insertHtml converts string to DOM nodes
        Ext.DomHelper.insertHtml('afterEnd', container.dom, o.responseText);
        var newItem = Ext.get(Ext.get(container).getNextSibling());

        // delete original container
        container.remove();

        // highlight
        newItem.highlight();

        // re-up liveEdit behaviors on new element
        OC.breatheLife(newItem);
    }
    function _afterFailure(o) {
        OC.debug('Oops! There was a problem.\n\n' + o.responseText); 
    }

    // cancel link
    if (cancel) {
        function _cancelClick(e, el, o) {
            value.show();
            form.hide();
            container.removeClass('oc-liveEdit-editing');
            YAHOO.util.Event.stopEvent(e);
            //TODO: clear form
        }
        cancel.on('click', _cancelClick, this);
    }
    return this;
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

} // end OC.SearchLinks();

/* 
#
# Close Buttons
#
 */
OC.CloseButton = function(extEl) {
    // get references.  No ID naming scheme.  just use parent node.
    var closeButton = extEl;
    var container = Ext.get(closeButton.dom.parentNode);
    container.setVisibilityMode(Ext.Element.DISPLAY);

    //behaviors
    function _closeButtonClick(e, el, o) {
        if (confirm('are you sure?')) {
            //ajax call

            //fade out
            container.fadeOut({});
        }
        YAHOO.util.Event.stopEvent(e);
    }
    closeButton.on('click', _closeButtonClick, this);
    
    return this;
}

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
}

/* 
#
# Expanders
#
 */
OC.Expander = function(extEl) {
    // get references. 
    var container = extEl;
    var expanderLink = Ext.get(Ext.query(".oc-expander-link", container.dom)[0]);
    var title = expanderLink.dom.innerHTML;
    var content = Ext.get(Ext.query(".oc-expander-content",  container.dom)[0]);

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
      expanderLink.dom.innerHTML = "[x] Close";
    }
    function _contract() {
      content.slideOut('t',{duration: .1});
      container.removeClass('oc-expander-open');
      expanderLink.dom.innerHTML = title;
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
    
    // init (when breatheLife is called)
    if (!container.hasClass('oc-expander-open')) {
      _contract();
    }
    
    return this;
}

/*
#
# Register Form
#
 */
OC.JoinForm = function(extEl) {
    // setup references
    var form = Ext.get('oc-join-form');
    var usernameField = Ext.get('__ac_name');
    var usernameValidator = Ext.get('oc-username-validator');
    // hacking this together for the moment.

    //check references
    if (!form || !usernameField || !usernameValidator)
        return;

    //username field   
    function _usernameKeyPress(e, el, o) {
        //setup request
        var options = {
           url: 'user-exists',
           method:'post',
           params:{username: usernameField.dom.value},
           callback: function(options, bSuccess, response) {
               if (bSuccess) {
                   if( response.responseText )
                       usernameValidator.update('no good');
                   else
                       usernameValidator.update('ok!');
               }
           },
           scope: this
        };
        // make ajax call
        new Ext.data.Connection().request(options);
    }
    usernameField.on('keypress', _usernameKeyPress, this);
    
    return this;
}

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
}

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
  ".oc-selectBoxAutoLinks" : "SelectBoxAutoLinks",
  ".oc-expander" : "Expander",
  "#version_compare_form" : "HistoryList",
  "#oc-join-form" : "JoinForm",
  ".oc-liveForm" : "LiveForm",
  ".oc-liveItem" : "LiveItem"
}
    
/* 
#
# breathes life (aka js behaviors) into HTML elements.
# call this on load w/ no argument to breathe life to entire document.
# When adding new nodes to the dom, call breatheLife(newItem) to activate that element and it's children.
#
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

} // OC.breatheLife()

/*
#------------------------------------------------------------------------
# Utilities
#------------------------------------------------------------------------
*/

// Debug Function.  Turn off for live code or IE
OC.debug = function(string) {
  var method = "console"; /* "console", "alert" or "" */
  switch (method) {
    case "console" :
      console.log(string);
      break;
    case "alert" :
      alert(string);
      break;
    default:
      return;
  }
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
  var checkAll = Ext.select('#' + liveForm.dom.id + " .oc-checkAll" )
  var liveItems = Ext.select('#' + liveForm.dom.id + " .oc-liveItem" )

  // check required refs
  if (!liveForm) {
    OC.debug("LiveForm: couldn't get element references")
    return;
  }  else {
    OC.debug('LiveForm: Got element references');
  }
  
  // properties
  var updater = {
    task : null,
    target : null
  }
  var requestData = null; /* request params, once an action happens */
    
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
    return updater;
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
  
  // action links
  if (actionLinks) {
    actionLinks.removeAllListeners();;
    function _actionLinkClick(e, el, o) {
      YAHOO.util.Event.stopEvent(e);
      
      // get action/href & split action from params
      var action = el.href.split("?")[0];
      requestData = el.href.split("?")[1];
      
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
    
  // form submit
  function _formSubmit(e, el, o) {
    OC.debug("_formSubmit");
    requestData = YAHOO.util.Connect.setForm(liveForm.dom);
    YAHOO.util.Event.stopEvent(e);
    var action = liveForm.dom.action;
    var cObj = YAHOO.util.Connect.asyncRequest("POST", action, 
      { success: _afterSuccess, 
        failure: _afterFailure, 
        scope: this 
      },
      "mode=async"
    );
  }
  liveForm.removeAllListeners();
  liveForm.on('submit', _formSubmit, this);
  
  // after success
  function _afterSuccess(o) {
    OC.debug('_afterSuccess');
    updater = _getUpdater(requestData);
    OC.debug('updater.task: ' + updater.task);
    
    switch (updater.task) {
      case "update" :
        // replace element
        var response = eval( "(" + o.responseText + ")" );
        
        /* FIXME: What if this is an error page? (404, need login, etc) */
        
        for (elId in response) {
          var target = Ext.get(elId);
          var html = Ext.util.Format.trim(response[elId]);
          var newNode = Ext.DomHelper.insertHtml("beforeBegin", target.dom, html);
          target.remove();
          Ext.get(newNode).highlight();
          OC.breatheLife(newNode);
        }
      break;
      
      case "delete" :
        // Don't use updater.target here.  Server will pass back IDs to delete.
        
        // Create Array from o.responseText
        var IDs = eval(o.responseText);
        
        for (var i = 0; i<IDs.length; i++) {
          _removeItem(IDs[i]);
        }

      break;
      
    } 
  }
  
  // after failure
  function _afterFailure(o) {
    OC.debug('_afterFailure');
  }
  
  // remove item
  function _removeItem(id) {
    var extEl = Ext.get(id);
    extEl.fadeOut({remove: true, useDisplay: true});
    
    // to do: send user message w/ undo link
  }
}

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
      
      function _valueClick(e,el,o) {
        //_toggleForm();
      }
      value.on('click', _valueClick, this);
      
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
        
        //turn into a real object. CAREFUL - only do this with trusted content
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
          OC.debug(o.responseText);
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
    
    //clear listeners. Temporary as elements can be made liveItems repeatedly right now. 
    container.removeAllListeners();
    value.removeAllListeners();
    edit.removeAllListeners();
    delete_.removeAllListeners();
    form.removeAllListeners();
    cancel.removeAllListeners();

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
OC.SelectBoxAutoLinks = function(extEl) {
    // get references.  No ID naming scheme yet.  just use parent node.
    var select = extEl;
    var submit = Ext.get(Ext.query('input[type=submit]', select.dom.parentNode)[0]);

    //submit 
    submit.setVisibilityMode(Ext.Element.DISPLAY);
    submit.hide();

    //behaviors
    function _selectChange(e, el, o) {
        window.location = el.value;
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
        userMessage.update("Please select exactly 2 versions to compare.");
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

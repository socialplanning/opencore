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
  ".oc-updateForm" : "UpdateForm",
  ".oc-liveAction" : "LiveAction",
  ".oc-liveEdit" : "LiveEdit",
  ".oc-close" : "CloseButton",
  ".oc-dropdown-links" : "DropDownLinks",
  ".oc-expander" : "Expander",
  "#version_compare_form" : "HistoryList",
  "#oc-join-form" : "JoinForm",
  ".oc-liveForm" : "LiveForm"
}
    
/* 
#
# breathes life (aka js behaviors) into HTML elements.
# call this on load, and again each time we add new stuff to the DOM.  
#
*/
OC.breatheLife = function() {
  // loop through selectors specified above
  for (var selector in OC.liveElementKey) {
    
    // within each query, loop through each Ext Element and check if there's an object        
    var elements = Ext.query(selector);
    if(elements.length > 0){
      
      for (var i = 0; i < elements.length; i++) {
      
        //get an Ext Obj for your element
        var extEl = Ext.get(elements[i]);
        
        // check if an object already exists for this.  If not, create one.
        if (OC.liveElements[extEl.dom.id])
          continue;
        
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
# Classes - will become liveElement objects
#------------------------------------------------------------------------
*/

/*
#
# Live Form
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
    OC.debug("couldn't get element references")
    return;
  }  else {
    OC.debug('Got element references');
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
  
  // live items
  if (liveItems) {
    liveItems.each(function(extEl) {
      // get references
      var value = Ext.get(Ext.query('.oc-liveItem-value', extEl.dom)[0]); 
      var editForm = Ext.get(Ext.query('.oc-liveItem-editForm', extEl.dom)[0]);
      var toggleLinks = Ext.select(Ext.query('.oc-liveItem_toggle', extEl.dom))
      
      if (!value || !editForm) {
        OC.debug("liveItems.each: Couldn't get element refs");
        return;
      }
      
      // hide edit form
      editForm.setVisibilityMode(Ext.Element.DISPLAY);
      editForm.hide();
      
      // toggle link
      function _toggleLinksClick(e, el, o) {
        YAHOO.util.Event.stopEvent(e);
        value.toggle();
        editForm.toggle();
      }
      toggleLinks.on('click', _toggleLinksClick, this);
      
    }, this);
  }
  
  // action links
  if (actionLinks) {
    function _actionLinkClick(e, el, o) {
      YAHOO.util.Event.stopEvent(e);
      
      // get action/href & split action from params
      var action = el.href.split("?")[0];
      requestData = el.href.split("?")[1];
      
      var requestUri = el.href + "mode=async";
      
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
    var action = "backend.php"; /* will be form.dom.action once we move to NUI  */
    var cObj = YAHOO.util.Connect.asyncRequest("POST", action, 
      { success: _afterSuccess, 
        failure: _afterFailure, 
        scope: this 
      },
      "mode=async"
    );
  }
  liveForm.on('submit', _formSubmit, this);
  
  // after success
  function _afterSuccess(o) {
    OC.debug('_afterSuccess');
    updater = _getUpdater(requestData);
    OC.debug('updater.task: ' + updater.task);
    OC.debug('updater.target: ');
    OC.debug(updater.target.dom)
    
    switch (updater.task) {
      case "update" :
      // replace element
      o.responseText = Ext.util.Format.trim(o.responseText);
      var newNode = Ext.DomHelper.insertHtml("beforeBegin", updater.target.dom, o.responseText);
      updater.target.remove();
      Ext.get(newNode).highlight();
      break;
      
      case "delete" :
        if (updater.target == "batch") {  // delete group of elements
          
          var items = o.responseText.split('&');
          for (var i = 0; i<items.length; i++) {
            _removeItem(Ext.select('#' + items[i]));
          }
          
        } else {  // delete single element
          
          _removeItem(updater.target);
        }
      break;
      
    } 
    
    OC.breatheLife();
  }
  
  // after failure
  function _afterFailure(o) {
    OC.debug('_afterFailure');
  }
  
  // remove item
  function _removeItem(extEl) {
    extEl.fadeOut({remove: true, useDisplay: true});
    
    // to do: send user message w/ undo link
  }
}


/* 
#
# OC Update Form
# 
*/
OC.UpdateForm = function(extEl) {
    OC.debug('OC.UpdateForm');
    //get references
    this.form = extEl;
    this.targetId = Ext.get(Ext.query('input[name=oc-target]',extEl.dom)[0]).dom.value;
    this.target = Ext.get(this.targetId);
    this.indicator = Ext.get(Ext.query('.oc-indicator',extEl.dom)[0]);
    this.submit = Ext.get(Ext.query('input[type=submit]',extEl.dom)[0])

    //check refs
    if (!this.form || !this.target || !this.indicator || !this.submit) {
        OC.debug('element missing');
        return;
    }

    //vars & settings
    this.isUpload = false;
    if (this.form.dom.enctype)
        this.isUpload = true;
    OC.debug(this.form.dom.enctype);
    this.indicator.setVisibilityMode(Ext.Element.DISPLAY);
    this.indicator.hide();

    // loading
    this.startLoading = function() {
        this.indicator.show();
        this.submit.dom.disabled = true;
        this.submit.originalValue = this.submit.dom.value;
        this.submit.dom.value = "Please wait..."
    }
    this.stopLoading = function() {
        this.indicator.hide();
        this.submit.dom.disabled = false;
        this.submit.dom.value = this.submit.originalValue;
        this.form.dom.reset();
    }

    //ajax request
    this.formSubmit = function(e, el, o) {
                
        if (this.isUpload)
            YAHOO.util.Connect.setForm(el, true);
        else 
            YAHOO.util.Connect.setForm(el);

        var callback = {
          success: this.afterSuccess,
          upload: this.afterUpload,
          failure: this.afterFailure,
          scope: this
        }
	OC.debug(this.form.dom.action);
        var cObj = YAHOO.util.Connect.asyncRequest("POST", this.form.dom.action, callback);
        this.startLoading();
        
        YAHOO.util.Event.stopEvent(e);

    }
    this.form.on('submit', this.formSubmit, this);

    // after request
    this.afterUpload = function(o) {
        this.stopLoading(); 
        
        //turn into a real object. CAREFUL - only do this with trusted content
        var response = eval( '(' + o.responseText + ')' );
        
        switch (response.status) {
          case "success" :
            this.afterUploadSuccess(response);
          break;
          case "failure" :
            this.afterUploadFailure(response);
          break;
          default:
            OC.debug('default');
        } 
    }
    this.afterUploadSuccess = function(response) {
      OC.debug('this.afterUploadSuccess');
      OC.debug(response);
      
      //2nd ajax request
      var cObj = YAHOO.util.Connect.asyncRequest("GET", response.updateURL, { 
        success: function(o) {
          
          // insert new - DomHelper.insertHtml converts string to DOM nodes
          OC.debug(o.responseText);
          o.responseText = Ext.util.Format.trim(o.responseText);
          var newItem = Ext.get(Ext.DomHelper.insertHtml('beforeEnd', this.target.dom, o.responseText));
          newItem.highlight("ffffcc", { endColor: "eeeeee"});

          //re-up behaviors on new element
          OC.breatheLife();
        }, 
        failure: function(o) {
          OC.debug('upload failed');
        },
        scope: this 
      });
      
      
    }

    this.afterFailure = function(o) {
        OC.debug('this.afterFailure RESPONSE BELOW:\n\n');
        for (prop in o) {
          OC.debug(prop + ":");
          OC.debug(o["" + prop + ""]);
        }
    }
    this.afterSuccess = function(o) {
        OC.debug('this.afterSuccess RESPONSE BELOW:\n\n'); 
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
    this.container = extEl;
    this.value = Ext.select(Ext.DomQuery.select('.oc-liveEdit-value',this.container.dom));
    this.edit = Ext.get(Ext.query('.oc-liveEdit-edit', this.container.dom)[0]);
    this.delete_ = Ext.get(Ext.query('.oc-liveEdit-delete', this.container.dom)[0]);
    this.form = Ext.get(Ext.query('.oc-liveEdit-form', this.container.dom)[0]);
    this.cancel = Ext.get(Ext.query('.oc-liveEdit-cancel', this.container.dom)[0]);

    // check to make sure we have what we need
    //if(!this.container || !this.value || !this.form)
    //    return;

    OC.debug(this.form.dom);

    /*
     # Attach Behviors
     */
    // container
    this.containerMouseOver = function(e, el, o) {
        this.container.addClass('oc-liveEdit-hover');
        this.value.addClass('oc-liveEdit-hover');
    }
    this.container.on('mouseover', this.containerMouseOver, this);

    this.containerMouseOut = function(e, el, o) {
        this.container.removeClass('oc-liveEdit-hover');
        this.value.removeClass('oc-liveEdit-hover');
    }
    this.container.on('mouseout', this.containerMouseOut, this);
    /*
       this.containerClick = function(e, el, o) {
       this.value.hide();
       this.form.show();
       this.container.addClass('oc-liveEdit-editing');
       }
       this.container.on('click', this.containerClick, this);
     */
    //edit
    this.editClick = function(e, el, o) {
        YAHOO.util.Event.stopEvent(e);
        this.value.hide();
        this.form.show();
        this.container.addClass('oc-liveEdit-editing');
    }
    if (this.edit) {
        this.edit.on('click', this.editClick, this);
    }

    this.deleteClick = function(e, el, o) {
        YAHOO.util.Event.stopEvent(e);
        if (confirm("Are you sure you want to delete?")) {
            YAHOO.util.Connect.setForm(this.form.dom);
            var action = this.form.dom.action.replace(/(.*)update/, '$1delete');
            var cObj = YAHOO.util.Connect.asyncRequest("POST", action, { success: this.afterDelete, failure: this.afterFailure, scope: this });
        }            
    }
    if (this.delete_) {
        this.delete_.on('click', this.deleteClick, this);
    }


    //value
    this.value.setVisibilityMode(Ext.Element.DISPLAY);

    //form
    this.form.setVisibilityMode(Ext.Element.DISPLAY);
    this.form.hide();

    //ajax request
    this.formSubmit = function(e, el, o) {
        YAHOO.util.Connect.setForm(el);
        var cObj = YAHOO.util.Connect.asyncRequest("POST", el.action, { success: this.afterSuccess, failure: this.afterFailure, scope: this });
        YAHOO.util.Event.stopEvent(e);
    }
    this.form.on('submit', this.formSubmit, this);

    // after request

    this.afterDelete = function(o) {
        // delete original container
        this.container.setVisibilityMode(Ext.Element.DISPLAY);
        this.container.dom.style.backgroundColor = "red";
        this.container.fadeOut();
    }

    this.afterSuccess = function(o) {

        // insert new - DomHelper.insertHtml converts string to DOM nodes
        Ext.DomHelper.insertHtml('afterEnd', this.container.dom, o.responseText);
        var newItem = Ext.get(Ext.get(this.container).getNextSibling());

        // delete original container
        this.container.remove();

        // highlight
        newItem.highlight();

        // re-up liveEdit behaviors on new element
        OC.breatheLife();
    }
    this.afterFailure = function(o) {
        OC.debug('Oops! There was a problem.\n\n' + o.responseText); 
    }

    // cancel link
    if (this.cancel) {
        this.cancelClick = function(e, el, o) {
            this.value.show();
            this.form.hide();
            this.container.removeClass('oc-liveEdit-editing');
            YAHOO.util.Event.stopEvent(e);
            //TODO: clear form
        }
        this.cancel.on('click', this.cancelClick, this);
    }
    return this;
}

/* 
#
# LiveAction
#
*/
OC.LiveAction = function(extEl) {
    // get references
    this.container = extEl;
    this.actionLinks = Ext.select(Ext.DomQuery.select('.oc-liveAction-actionLink',this.container.dom));

    // settings
    this.container.setVisibilityMode(Ext.Element.DISPLAY);
    
    //behaviors
    this.actionLinkClick = function(e, el, o) {
      YAHOO.util.Event.stopEvent(e);
      if (confirm('are you sure?')) {
          //ajax call

          //fade out
          this.container.fadeOut({});
      }
    }
    this.actionLinks.on('click', this.actionLinkClick, this);
    
    return this;
}

/* 
#
# Close Buttons
#
 */
OC.CloseButton = function(extEl) {
    // get references.  No ID naming scheme.  just use parent node.
    this.closeButton = extEl;
    this.container = Ext.get(this.closeButton.dom.parentNode);
    this.container.setVisibilityMode(Ext.Element.DISPLAY);

    //behaviors
    this.closeButtonClick = function(e, el, o) {
        if (confirm('are you sure?')) {
            //ajax call

            //fade out
            this.container.fadeOut({});
        }
        YAHOO.util.Event.stopEvent(e);
    }
    this.closeButton.on('click', this.closeButtonClick, this);
    
    return this;
}

/* 
#
# Dropdown Links
#
 */
OC.DropDownLinks = function(extEl) {
    // get references.  No ID naming scheme yet.  just use parent node.
    this.select = extEl;
    this.submit = Ext.get(Ext.query('input[type=submit]', extEl.dom.parentNode)[0]);

    //submit 
    this.submit.setVisibilityMode(Ext.Element.DISPLAY);
    this.submit.hide();

    //behaviors
    this.selectChange = function(e, el, o) {
        window.location = el.value;
    } 
    this.select.on('change', this.selectChange, this);
    
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
    if(!container || !expanderLink || !content)
        return;

    //link
    function linkClick(e, el, o) {
        //fade out
        if (!content.isVisible()) {
            content.slideIn('t',{duration: .1});
            container.addClass('oc-expander-open');
            expanderLink.dom.innerHTML = "[x] Close";
        } else {
            content.slideOut('t',{duration: .1});
            container.removeClass('oc-expander-open');
            expanderLink.dom.innerHTML = title;
        } 

        YAHOO.util.Event.stopEvent(e);
    }
    expanderLink.on('click', linkClick, this);

    //contents 
    content.setVisibilityMode(Ext.Element.DISPLAY);
    content.hide();
    
    return this;
}

/*
#
# Register Form
#
 */
OC.JoinForm = function(extEl) {
    // setup references
    this.form = Ext.get('oc-join-form');
    this.usernameField = Ext.get('__ac_name');
    this.usernameValidator = Ext.get('oc-username-validator');
    // hacking this together for the moment.

    //check references
    if (!this.form || !this.usernameField || !this.usernameValidator)
        return;

    //username field   
    this.usernameKeyPress = function(e, el, o) {
        //setup request
        var options = {
           url: 'user-exists',
           method:'post',
           params:{username:this.usernameField.dom.value},
           callback: function(options, bSuccess, response) {
               if (bSuccess) {
                   if( response.responseText )
                       this.usernameValidator.update('no good');
                   else
                       this.usernameValidator.update('ok!');
               }
           },
           scope: this
        };
        // make ajax call
        new Ext.data.Connection().request(options);
    }
    this.usernameField.on('keypress', this.usernameKeyPress, this);
    
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

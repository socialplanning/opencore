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

// where we'll store all our live elements
OC.liveElements = new Array();
    
/* 
#
# how we know which elements get which features
# css or xpath selector : OC Object name (without OC.)
#
*/
OC.liveElementKey = {
  ".oc-updateForm" : "UpdateForm",
  ".oc-liveEdit" : "LiveEditForm",
  ".oc-close" : "CloseButton",
  ".oc-dropdown-links" : "DropDownLinks",
  ".oc-expander" : "Expander",
  "#oc-wiki-history" : "HistoryList",
  "#oc-join-form" : "JoinForm"
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
      
      //2nd ajax request
      var cObj = YAHOO.util.Connect.asyncRequest("GET", response.updateURL, { 
        success: function(o) {
          
          // insert new - DomHelper.insertHtml converts string to DOM nodes
          OC.debug(o.responseText);
          o.responseText = Ext.util.Format.trim(o.responseText);
          var newItem = Ext.get(Ext.DomHelper.insertHtml('beforeEnd', this.target.dom, o.responseText));
          newItem.highlight("ffffcc", { endColor: "eeeeee"});

          //re-up liveEdit behaviors on new element
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
OC.LiveEditForm = function(extEl) {
    //get references for included elements
    this.container = extEl;
    this.value = Ext.get(Ext.query('.oc-liveEdit-value', extEl.dom)[0]);
    this.edit = Ext.get(Ext.query('.oc-liveEdit-edit', extEl.dom)[0]);
    this.delete = Ext.get(Ext.query('.oc-liveEdit-delete', extEl.dom)[0]);
    this.form = Ext.get(Ext.query('.oc-liveEdit-form', extEl.dom)[0]);
    this.cancel = Ext.get(Ext.query('.oc-liveEdit-cancel', extEl.dom)[0]);

    // check to make sure we have what we need
    if(!this.container || !this.value || !this.form)
        return;

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
    if (this.delete) {
        this.delete.on('click', this.deleteClick, this);
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
    this.container = extEl;
    this.expanderLink = Ext.get(Ext.query(".oc-expander-link", this.container.dom)[0]);
    this.content = Ext.get(Ext.query(".oc-expander-content",  this.container.dom)[0]);

    // check to make sure we have everything
    if(!this.container || !this.expanderLink || !this.content)
        return;

    //link
    this.linkClick = function(e, el, o) {
        //fade out
        if (!this.content.isVisible()) {
            this.content.slideIn('t',{duration: .1});
            this.container.addClass('oc-expander-open');
        } else {
            this.content.slideOut('t',{duration: .1});
            this.container.removeClass('oc-expander-open');
        } 

        YAHOO.util.Event.stopEvent(e);
    }
    this.expanderLink.on('click', this.linkClick, this);

    //contents 
    this.content.setVisibilityMode(Ext.Element.DISPLAY);
    this.content.hide();
    
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
    this.form = extEl;
    this.compare = Ext.get(Ext.select('#' + extEl.dom.id + ' input[type=submit]'));
    this.versions  = Ext.get(Ext.select('#' + extEl.dom.id + ' li'));
    this.checkboxes = Ext.get(Ext.select('#' + extEl.dom.id + ' input[type=checkbox]'));
   
    //check references
    if (!this.form || !this.compare || !this.versions)
        return;
    
    //compare buttons
    this.enableCompareButtons = function() {
      this.compare.each(function(el){
        el.dom.disabled = false;
      });
    }
    this.disableCompareButtons = function() {
      this.compare.each(function(el){
        el.dom.disabled = true;
      });
    }
    this.disableCompareButtons();
    
    //checkboxes
    this.clearCheckboxes = function() {
      this.checkboxes.each(function(el) {
          el.dom.checked = false;
          Ext.get(el.dom.parentNode).removeClass('oc-selected');
      });
    }
    this.checkboxesClick = function(e, el, o) {
      //count # checked
      var numChecked = 0;
      this.checkboxes.each(function(el) {
        if (el.dom.checked) {
          numChecked++;
        }
      });
      
      //if more than 2, clear all and check currentStyle
      if (numChecked > 2) {
        this.clearCheckboxes();
        el.checked = true;
      }
      
      //if exactly 2, enable compare buttons
      if (numChecked == 2) {
        this.enableCompareButtons();
      } else {
        this.disableCompareButtons();    
      }
      
      //highlight this checkbox's parent
      if (el.checked)
        Ext.get(el.parentNode).addClass('oc-selected');
      else
        Ext.get(el.parentNode).removeClass('oc-selected');
    }
    this.checkboxes.on('click', this.checkboxesClick, this)
    
    OC.debug(this.form.dom.elements);
    
    return this;
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

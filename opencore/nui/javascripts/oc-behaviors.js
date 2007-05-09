/* Behaviors */

	/*
	#
	# OC object - elements we'll use, settings
	#
	*/
	function OC() {
		this.liveEditForms = new Array();
		this.closeButtons = new Array();
		this.expanders = new Array();
		this.dropDownLinks = new Array();
		//this.wikiTabs = new Array();
		this.registerForm;
	}
	var OC = new OC();

	/*
	#
	# Live Edit Forms
	#
	*/
	function LiveEditForm (elId) {
		//parse elId and get base & id
		this.base = parseId().base;
		this.id = parseId().id;
		
		function parseId() {
			/* IDs should follow the form: base_type_id (e.g., liveEdit_value_12) */
			results = new Array();
			results.base = elId.split('_')[0];
			results.id = elId.split('_')[2];
			return results;
		}
		
		//get references for included elements
		this.container = Ext.get(this.base + "_container_" + this.id);
		this.value = Ext.get(this.base + "_value_" + this.id);
		this.form = Ext.get(this.base + "_form_" + this.id);
		this.selectBoxes = Ext.query("#" + elId + " select");  //quick for demo.		
		this.selectBox = Ext.get(this.selectBoxes[0]); //quick for demo.
		
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
		
		this.containerClick = function(e, el, o) {
			this.value.hide();
			this.form.show();
			this.container.addClass('oc-liveEdit-editing');
		}
		this.container.on('click', this.containerClick, this);
		
		//value
		this.value.setVisibilityMode(Ext.Element.DISPLAY);
		
		//form
		this.form.setVisibilityMode(Ext.Element.DISPLAY);
		this.form.hide();
		
		//select
		// temp.  this will change to be a smarter query.
		this.selectBoxChange = function (e, el, o){
			//show/hide
			this.value.show();
			this.form.hide();
			
			//do an ajax call
			
			//update the target
			this.value.update(el.value);
			
			//highlight
			this.container.removeClass('oc-liveEdit-editing');
			this.container.highlight('c6ff80', { endColor: 'ffffff' });
		}
		this.selectBox.on('change', this.selectBoxChange, this);
				
	}
	
	/* 
	#
	# Close Buttons
	#
	*/
	function CloseButton (el) {
		// get references.  No ID naming scheme yet.  just use parent node.
		this.closeButton = Ext.get(el);
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
		this.closeButton.on('click', this.closeButtonClick, this)
	}
	
	/* 
	#
	# Dropdown Links
	#
	*/
	function DropDownLinks (el) {
		// get references.  No ID naming scheme yet.  just use parent node.
		this.select = Ext.get(el);
		this.submit = Ext.get(Ext.query('input[type=submit]', el.parentNode)[0]);
				
		//submit 
		this.submit.setVisibilityMode(Ext.Element.DISPLAY);
		this.submit.hide();
		
		//behaviors
		this.selectChange = function(e, el, o) {
      window.location = el.value;
		} 
		this.select.on('change', this.selectChange, this)
	}
	
	/* 
	#
	# Expanders
	#
	*/
	function Expander (el) {
		// get references. 
		this.container = Ext.get(el);
		this.expanderLink = Ext.get(Ext.query(".oc-expander-link", this.container.dom)[0]);
		this.content = Ext.get(Ext.query(".oc-expander-content",  this.container.dom)[0]);
		
		// check to make sure we have everything
		if(!this.container || !this.expanderLink || !this.content)
		  return;
				
		//link
		this.linkClick = function(e, el, o) {
			//fade out
			if (!this.content.isVisible())
			  this.content.slideIn('t',{duration: .1});
		  else 
		    this.content.slideOut('t',{duration: .1});
		    
			YAHOO.util.Event.stopEvent(e);
		}
		this.expanderLink.on('click', this.linkClick, this);
		
		//contents 
		this.content.setVisibilityMode(Ext.Element.DISPLAY);
		this.content.hide();
	}
	
	/* 
	#
	# WikiTabs
	#
	*/
	function WikiTab (el) {
		// get references. 
		this.tab = Ext.get(el);
		this.wikiEdit = Ext.get(Ext.select(".oc-wiki-edit"));
		this.wikiContent = Ext.get(Ext.select(".oc-wiki-content"));
		this.wikiHistory = Ext.get(Ext.select(".oc-wiki-history"));
		
		//check to make sure we've got everything
		if (!this.tab || !this.wikiEdit || !this.wikiContent || !this.wikiHistory)
		  return;
		
		// content box
		this.wikiContent.setVisibilityMode(Ext.Element.DISPLAY);
		
		// edit box
		this.wikiEdit.setVisibilityMode(Ext.Element.DISPLAY);
		this.wikiEdit.hide();
		
		// history box
		this.wikiHistory.setVisibilityMode(Ext.Element.DISPLAY);
		this.wikiHistory.hide();
		
		// view tab				
		this.viewClick = function(e, el, o) {
			this.wikiEdit.hide();
			this.wikiContent.show();
			this.wikiHistory.hide();
			Ext.select('.oc-tabs li a').removeClass('oc-selected');
			Ext.get(el).addClass('oc-selected');
			YAHOO.util.Event.stopEvent(e);
		}
		if (el.rel == "view") {
		  this.tab.addClass('oc-selected');
			this.tab.on('click', this.viewClick, this);
		} 
		
		//edit tab
		this.editClick = function(e, el, o) {
			this.wikiEdit.show();
			this.wikiContent.hide();
			this.wikiHistory.hide();
			Ext.select('.oc-tabs li a').removeClass('oc-selected');
			Ext.get(el).addClass('oc-selected');
			YAHOO.util.Event.stopEvent(e);
		}
		if (el.rel == "edit") {
			this.tab.on('click', this.editClick, this);
		} 
		
		// history tab
		this.historyClick = function(e, el, o) {
			this.wikiEdit.hide();
			this.wikiContent.hide();
			this.wikiHistory.show();
			Ext.select('.oc-tabs li a').removeClass('oc-selected');
			Ext.get(el).addClass('oc-selected');
			YAHOO.util.Event.stopEvent(e);
		}
		if (el.rel == "history") {
			this.tab.on('click', this.historyClick, this);
		}	
	}
	
	/*
	#
	# Register Form
	#
	*/
	function RegisterForm() {
	  // setup references
    this.form = Ext.get('oc-register-form');
    this.usernameField = Ext.get('__ac_name');
    this.usernameValidator = Ext.get('oc-username-validator');
    
    //check references
    if (!this.form || !this.usernameField || !this.usernameValidator)
      return;
    
    this.usernameKeyPress = function(e, el, o) {
      
      //setup request
      var options = {
         url: 'register'
         , method:'get'
         , callback: function(options, bSuccess, response) {
             if (bSuccess)
              this.usernameValidator.update('yes');
         }
         , scope: this
      };
      new Ext.data.Connection().request(options);
    }
    this.usernameField.on('keypress', this.usernameKeyPress, this)
	}
		
  		
	//Load Em up
	Ext.onReady(function() {
			
		// Find each live edit form and make an array of LiveEditForm objects
		Ext.query('.oc-liveEdit-container').forEach(function(el) {
			OC.liveEditForms.push(new LiveEditForm(el.id));
		});	
		
		// Find close buttons and make them CloseButton objects
		Ext.query('.oc-close').forEach(function(el) {
			OC.closeButtons.push(new CloseButton(el));
		});
		
		// Find drop down links and make them DropDownLinks objects
		Ext.query('.oc-dropdown-links').forEach(function(el) {
			OC.dropDownLinks.push(new DropDownLinks(el));
		});
		
		// Find expanders and make them Expander objects
		Ext.query('.oc-expander').forEach(function(el) {
			OC.expanders.push(new Expander(el));
		});
		
		// Find wiki tabs and make them wikiTab objects
		//Ext.query('.oc-tabs li a').forEach(function(el) {
		//	OC.wikiTabs.push(new WikiTab(el));
		//});
		
		// Find login form and make LoginForm object
		if (Ext.get('oc-register-form')) {
			OC.registerForm = new RegisterForm();
		}
							
	}); // onReady
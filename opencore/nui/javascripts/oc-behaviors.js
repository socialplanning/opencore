/* Behaviors */

	/*
	#
	# OC object - elements we'll use, settings
	#
	*/
	function OC() {
		this.liveEditForms = new Array();
		this.closeButtons = new Array();
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
		
  		
	//Load Em up
	Ext.onReady(function() {
			
		// Find each live edit form and make an array of LiveEditForm objects
		Ext.query('.oc-liveEdit-container').forEach(function(el) {
			OC.liveEditForms.push(new LiveEditForm(el.id));
		});	
		
		// Find close butons and make them CloseButton objects
		Ext.query('.oc-close').forEach(function(el) {
			OC.closeButtons.push(new CloseButton(el));
		});
							
	}); // onReady
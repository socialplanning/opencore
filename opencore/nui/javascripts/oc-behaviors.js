/* Behaviors */

		// Utilities
  		var OC = {}
  		OC.util = {
  			parseId: function(elId) {
  				/* IDs should follow the form: base_type_id (e.g., liveEdit_value_12) */
  				var parsedId = new Array();
  				parsedId['base'] = elId.split('_')[0];
				parsedId['type'] = elId.split('_')[1];
				parsedId['id'] = elId.split('_')[2];
  				return parsedId;
  			}
  		}
  		
  		
  		//Extend Ded|Chain to allow looping over queries
		DED.extendChain('filter', function(f) {
		   this.el = this.el.filter(f);
		   return this;
		});
		DED.extendChain('do', function(f, a, override) {
		   YAHOO.util.DOM.batch(this.el, f, a, override);
		   return this;
		});
		
		//Live Edit Forms
		function LiveEditForm (elId) {
			//parse elId and get base & id
			this.base = parseId().base;
			this.id = parseId().id;
			
			//set IDs for form elements
			this.container = Ext.get(this.base + "_container_" + this.id);
			this.value = Ext.get(this.base + "_value_" + this.id);
			this.form = Ext.get(this.base + "_form_" + this.id);
			

			function parseId() {
				/* IDs should follow the form: base_type_id (e.g., liveEdit_value_12) */
				results = new Array();
				results.base = elId.split('_')[0];
				results.id = elId.split('_')[2];
				return results;
			}
			
			this.test = function() {
				//alert(this.container);
			}
		}
		
		
  		
  		//Behaviors
  		_$(window).on('load', function() {
				
			var liveEdit = new LiveEditForm('oc-liveEdit_container_12');
			liveEdit.test();
			
			var liveEdit2 = new LiveEditForm('oc-liveEdit_container_9');
			liveEdit2.test();
				
			//row mouseovers
			_$('tbody tr').on('mouseover', function(el,e) {
				_$(el).addClass('hover');
			});
			_$('tbody tr').on('mouseout', function(el,e) {
				_$(el).removeClass('hover');
			});
			
			//live edits
			_$('.oc-liveEdit-form').hide();
			_$('.oc-liveEdit').on('mouseover', function(el, e) {
				_$(el).addClass('oc-liveEdit-hover');
				_$("#" + el.id + " .oc-liveEdit-value").addClass('oc-liveEdit-hover');
			});
			_$('.oc-liveEdit').on('mouseout', function(el, e) {
				_$(el).removeClass('oc-liveEdit-hover');
				_$("#" + el.id + " .oc-liveEdit-value").removeClass('oc-liveEdit-hover');
			});
			_$('.oc-liveEdit-value').on('click', function(el,e){
				// TODO the whole live edit form should be an object.
				var parsedId = OC.util.parseId(el.id);
				var form = parsedId.base + '_form_' + parsedId.id;
				var container = parsedId.base + '_container_' + parsedId.id;
				
				_$(el).hide();
				_$('#' + form).show();							
			});
			_$('.oc-liveEdit-form select').on('change', function(el, e) {
				var parsedId = OC.util.parseId(el.parentNode.id);
				var form = parsedId.base + '_form_' + parsedId.id;
				var value = parsedId.base + '_value_' + parsedId.id;
				var container = parsedId.base + '_container_' + parsedId.id;
				
				//show/hide
				_$('#' + value).show();
				_$('#' + form).hide();
				
				//do an ajax call
				
				//update the target
				Ext.get(value).update(el.value);
				
				//highlight
				Ext.get(container).highlight('ffff9c', { endColor: 'ffffff' });
			});
			
		}); // end window load events
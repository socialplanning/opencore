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
  		
  		//Behaviors
  		_$(window).on('load', function() {
				
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
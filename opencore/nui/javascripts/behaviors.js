/* Behaviors */

_$(window).on('load', function() {
		
	//set up general behaviors
	_$('tbody tr').on('mouseover', function(el,e) {
		_$(el).addClass('hover');
	});
	_$('tbody tr').on('mouseout', function(el,e) {
		_$(el).removeClass('hover');
	});
}); // end window load events
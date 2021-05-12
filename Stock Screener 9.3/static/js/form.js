function set_estimate() {
	var inputs = [];
	var variables = ['a=', 'b=', 'c=', 'd=', 'e=', 'f=', 'g=', 'h=', 'i=', 'j='];
	$('input').each(function(index) {
		if (index < 3) {
			if ($(this).is(':checked')) {
				inputs.push(variables[index]+$(this).val().toString());
			} else {
				inputs.push(variables[index]);
			}
		} else {
			if (index != 10) {
				inputs.push(variables[index]+$(this).val().toString());
			}
		}
	})
	$.ajax({
		url : '/ajax?'+inputs.join('&'),
		success: function(estimate) {
			update(estimate);
		}
	});
}

function update(estimate) {
	$('#counter h1').text(estimate);
	if (estimate == 0) {
		$('#counter').css('border-color', '#ff0080');
	} else if (estimate <= 100) {
		$('#counter').css('border-color', '#00ff80');
	} else {
		$('#counter').css('border-color', '#eee');
	}
}

function set_value() {
	$('input[type=range]').each(function() {
		$(this).prev().children(":first").text($(this).val())
	})
}

function enable_mc() {
	if ($('.container input[type=checkbox]:checked').length > 0) {
		$('.container > span').css("color", "#333");
	} else {
		$('.container > span').css("color", "grey");
	}
}

function enable_input() {
	$('.input-container input[type=number]').each(function() {
		if ($(this).val()) {
			$(this).parent().prev().css("color", "#333");
		} else {
			$(this).parent().prev().css("color", "grey");
		}
	});
}

function enable_slider() {
	var enabled = [];
	$('.slider-container input[type=range]').each(function(index) {
		if ($(this).val() != '0') {
			$(this).prev().css('color', '#333');
			enabled.push('#slider'+(index+1).toString());
		} else {
			$(this).prev().css('color', 'grey');
		}
	});
	if (enabled.includes('#slider1') & enabled.includes('#slider2')) {
		document.querySelector('[data="test"]').innerHTML = '#slider1::-webkit-slider-thumb, #slider2::-webkit-slider-thumb { background: #00ff80 }';
	} else if (enabled.includes('#slider1')) {
		document.querySelector('[data="test"]').innerHTML = '#slider1::-webkit-slider-thumb { background: #00ff80 } #slider2::-webkit-slider-thumb { background: #ddd }';
	} else if (enabled.includes('#slider2')) {
		document.querySelector('[data="test"]').innerHTML = '#slider1::-webkit-slider-thumb { background: #ddd } #slider2::-webkit-slider-thumb { background: #00ff80 }';
	} else {
		document.querySelector('[data="test"]').innerHTML = '#slider1::-webkit-slider-thumb, #slider2::-webkit-slider-thumb { background: #ddd }';
	}
}

$(function() {
	set_estimate();
	set_value();
	enable_mc();
	enable_input();
	enable_slider();
	$('input[type=checkbox]').on('input', function() {
		set_estimate();
		enable_mc();
	});
	$('input[type=number]').on('input', function() {
		set_estimate();
		enable_input();
	});
	$('input[type=range]').on('change', function() {
		set_estimate();
		enable_slider();
	});
	$('input[type=range]').on('input', function() {
		set_value();
	});
})
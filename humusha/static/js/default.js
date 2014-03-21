(function($) {
		$(function() {
				// notifications
				$("form input[type=text]:first").focus();
				$("div#flashes div").fadeOut(7000, "easeOutBack");
				
				// switch language
				// $("#switch-language-form select").on("change", function() {
				//   $(this).parent().submit();
				// });
				// $('.carousel').carousel();
				
				$('#thesaurus ._parts ._content, #translations ._content').addClass('hide');
				
				$(document).on('click', '#thesaurus ._parts ._header, #translations ._header', function(e) {
						$(this).parent().find('._content').toggleClass('hide');
				});

				
		});
})(jQuery);

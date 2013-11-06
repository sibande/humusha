(function($) {
  $(function() {
    // notifications
    $("form input[type=text]:first").focus();
    $("div#flashes div").fadeOut(7000, "easeOutBack");
    
    // switch language
    // $("#switch-language-form select").on("change", function() {
    //   $(this).parent().submit();
    // });
    $('.carousel').carousel()
  });
})(jQuery);

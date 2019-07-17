// Login validation script
(function() {
  'use strict';
  window.addEventListener('load', function() {
    // Fetch all the forms we want to apply custom Bootstrap validation styles to
    var forms = document.getElementsByClassName('needs-validation');
    // Loop over them and prevent submission
    var validation = Array.prototype.filter.call(forms, function(form) {
      form.addEventListener('submit', function(event) {
        if (form.checkValidity() === false) {
          event.preventDefault();
          event.stopPropagation();
        }
        form.classList.add('was-validated');
      }, false);
    });
  }, false);
})();

let rows = document.querySelectorAll(".table tbody tr")

// Table row selection script		
$(rows).on("click", function(){
	$( this ).toggleClass("table-active")
})


      // Initially hide toggleable content
    $("td[colspan=3]").find("a").hide();

      // Click handler on entire table
    $("table").click(function(event) {

          // No bubbling up
        event.stopPropagation();

        var $target = $(event.target);

          // Open and close the appropriate thing
        if ( $target.closest("td").attr("colspan") > 1 ) {
            $target.find("a").slideToggle();
        } else {
            $target.closest("tr").next().find("a").slideToggle();
        }                    
    });

$(".update").click(function update(){
   	var selected_brewery = $(this).closest('tr').prev().children('.brewery').text()
   	var new_distributor = prompt("Enter a new distributor for " + selected_brewery + ":")
	
   	$.post( '/update/?brewery=' + selected_brewery, { new_distributor: new_distributor, selected_brewery: selected_brewery }, function(){
   		window.location.reload();
   		});

   	console.log(selected_brewery)
   	console.log(new_distributor)
});

$(".add").click(function add(){
		let selected_brewery = $(this).closest('tr').prev().children('.brewery').text()
		let new_beer = prompt("Add a new beer to " + selected_brewery + ":")

		$.post('/add_beer/?brewery=' + selected_brewery, { brewery: selected_brewery, new_beer: new_beer}, function(){
			alert("Added " + new_beer + " to " + selected_brewery + "!");
		});
});

$(".delete").click(function deleteBrewery(){
		let brewery = $(this).closest('tr').prev().children('.brewery').text()
		$.post('/delete_brewery', { brewery: brewery}, function(){
			window.location.reload()
		})
})

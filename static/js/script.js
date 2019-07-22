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

let rows = document.querySelectorAll(".view_all tbody tr")

// Table row selection script		
$(rows).on("click", function(){
	$( this ).toggleClass("table-active")
})


      // Initially hide toggleable content
    $("td[colspan=3]").find("a").hide();

      // Click handler on entire table
    $(".view_all").click(function(event) {

          // No bubbling up
        event.stopPropagation();

        var $target = $(event.target);

          // Open and close the appropriate thing
        if ( $target.closest("td").attr("colspan") > 1 ) {
            $target.find("a").slideToggle();
            $target.closest("tr").next().find("td").toggleClass("pb-1");

        } else {
            $target.closest("tr").next().find("a").slideToggle();
            $target.closest("tr").next().find("td").toggleClass("pb-1");
        }                    
    });

$(".update").click(function update(){
   	let selected_brewery = $(this).closest('tr').prev().children('.brewery').text()
   	let new_distributor = prompt("Enter a new distributor for " + selected_brewery + ":")
    $.ajax({
      url: '/breweries/' + selected_brewery,
      type: "PUT",
      data: { new_distributor: new_distributor, selected_brewery: selected_brewery },
      success: function(){
        alert(brewery + "distributor updated to " + new_distributor + "!")
        window.location.reload();
        }
    })
});


$(".add").click(function add(){
		let selected_brewery = $(this).closest('tr').prev().children('.brewery').text()
		let new_beer = prompt("Add a new beer to " + selected_brewery + ":")

		$.post('/breweries/' + selected_brewery + "/beers", { brewery: selected_brewery, new_beer: new_beer}, function(){
			alert("Added " + new_beer + " to " + selected_brewery + "!");
		});
});

$(".delete").click(function deleteBrewery(){
	let brewery = $(this).closest('tr').prev().children('.brewery').text()
  $.ajax({
    url: '/breweries/' + brewery,
    type: "DELETE",
    data: { brewery: brewery},
    success: function(){
      alert(brewery + " deleted!")
      window.location.reload()
    }
  })
});

$(".delete-beer").click(function deleteBeer(){
  let brewery = $(document).find('h1').text()
  let beer = $(document).find('h2').text()
  $.post('/delete_beer', {delete: beer}, function(){
    window.location.replace('/breweries/' + brewery)
    alert(beer + " deleted!")
  })
})


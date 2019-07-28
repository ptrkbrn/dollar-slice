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

let rows = document.querySelectorAll(".view_all tbody tr");

// Table row selection script   
$(rows).on("click", function(){
  $( this ).toggleClass("table-active");
});


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
    let selected_brewery = $(this).closest('tr').prev().children('.brewery').text();
    let new_distributor = prompt("Enter a new distributor for " + selected_brewery + ":");
    $.ajax({
      url: '/breweries/' + selected_brewery,
      type: "PUT",
      data: { new_distributor: new_distributor, selected_brewery: selected_brewery },
      success: function(){
        alert(selected_brewery + " distributor updated to " + new_distributor + "!");
        window.location.reload();
        }
    });
});


$(".add").click(function add(){
    let selected_brewery = $(this).closest('tr').prev().children('.brewery').text();
    let new_beer = prompt("Add a new beer to " + selected_brewery + ":");

    $.post('/breweries/' + selected_brewery + "/beers", { brewery: selected_brewery, new_beer: new_beer}, function(){
      alert("Added " + new_beer + " to " + selected_brewery + "!");
    });
});


// AJAX request for deleting brewery from list drop down
$(".delete").click(function deleteBrewery(){
  let brewery = $(this).closest('tr').prev().children('.brewery').text();
  let cfm = confirm("Are you sure you want to delete " + brewery + "?");
  if (cfm == true) {
    $.ajax({
      url: '/breweries/' + brewery,
      type: "DELETE",
      data: { brewery: brewery },
      success: function(){
        alert(brewery + " deleted!");
        window.location.reload();
      }
    });
  }
});

// Scripts for deleting brewery via the brewery delete page

// Prevents form submission
$("#delete-form").submit(function(e){
    return false;
});

// AJAX delete request
$( document ).ready(function(){
  $("#brewery-delete-btn").click(function deleteBrewery(){
    let brewery = $('#brewery').val();
    console.log(brewery);
    $.ajax({
      url: '/breweries/' + brewery,
      type: "DELETE",
      data: { brewery: brewery },
      success: function(){
        alert(brewery + " deleted!");
        window.location.replace('/breweries');
      }
    });
  });
});

// Scripts for deleteing beer via beer delete form

// Prevents form submission
$("#delete-beer-form").submit(function(e){
    return false;
});

$(".delete-beer-btn").click(function deleteThisBeer(){
  let brewery = $(document).find('h1').text();
  let beer = $( "#delete" ).val();
  console.log(brewery)
  console.log(beer)
  $.ajax({
    url: '/breweries/' + brewery + '/beers/' + beer,
    type: "DELETE",
    data: {beer: beer},
    dataType: "html",
    success: function(){
      window.location.load('/breweries/' + brewery);
    }
  });
});

// AJAX request for deleting beer via beer page
$(".delete-beer").click(function deleteBeer(){
  let brewery = $(document).find('h1').text();
  let beer = $(document).find('h2').text();
  $.ajax({
    url: '/breweries/' + brewery + '/beers/' + beer,
    type: "DELETE",
    data: {beer: beer},
    success: function(){
      window.location.replace('/breweries/' + brewery);
      alert(beer + " deleted!");
    }
  });
});

$('button[name="post_rating_Dialog"]').on('click', function(e) {
    var $form = $(this).closest('form');
    var csrf_token = document.querySelector('input[name="csrf_token"]').value
    var formData = new FormData();
    formData.append('csrf_token', csrf_token)
    e.preventDefault();
    $.ajax({
        url: $form.attr("action"),
        type: "GET",
        data:formData,
        contentType: false,
        processData: false,
        success: function(data){
            var rating_dialog_div = document.querySelector('div.users_rated_post')
            rating_dialog_div.innerHTML = data

            document.querySelector('li[name="likes"]').addEventListener("click", function(e){
                document.querySelector('li[name="dislikes"]').classList.remove("active");
                document.querySelector('li[name="likes"]').classList.add("active");
                document.querySelector('div[name="likes"]').style.display = "block"
                document.querySelector('div[name="dislikes"]').style.display = "none"
            });
            
            document.querySelector('li[name="dislikes"]').addEventListener("click", function(e){
                document.querySelector('li[name="dislikes"]').classList.add("active");
                document.querySelector('li[name="likes"]').classList.remove("active");
                document.querySelector('div[name="likes"]').style.display = "none"
                document.querySelector('div[name="dislikes"]').style.display = "block"
            });

            
            $('.post_rating_Dialog').modal({ keyboard: true })
            .one('click', '.confirmBtn', function() {
                $form.trigger('submit'); // submit the form
            })
            // .one() is NOT a typo of .on()
            .on('hidden.bs.modal', function () {
                $('.confirmBtn').unbind();
            });
        }
    })
    
});

